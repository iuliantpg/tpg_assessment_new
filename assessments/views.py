from django.shortcuts import render, redirect, get_object_or_404
from .models import Department, JobTitle, Competency, Question, Answer, InterviewSession, Scope, Category
from openai import OpenAI
from django.conf import settings
from django.http import JsonResponse

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def live_feedback(request):
    answer = request.GET.get('answer', '')
    position = request.GET.get('position', '')
    competency = request.GET.get('competency', '')
    question_text = request.GET.get('question', '')
    guidance = request.GET.get('guidance', '')
    if answer:
        feedback = get_openai_feedback(answer, position, competency, question_text, guidance)
        return JsonResponse({'feedback': feedback})
    return JsonResponse({'feedback': 'No answer provided.'})

def get_openai_feedback(answer, position, competency, question_text, guidance):
    prompt = (
        f"Position: {position}\n"
        f"Competency: {competency}\n"
        f"Question: {question_text}\n"
        f"Guidance: {guidance}\n"
        f"Answer: {answer}\n\n"
        "You are an executive assessor providing feedback on an interview answer. Focus strictly on whether the answer meets the interpretation guidance. "
        "This is an initial screening question, and more detailed questions will follow, so do not evaluate aspects like communication style, spelling, or depth unless directly relevant to the guidance."
        "Provide feedback in this format:"
        "1. Is the answer relevant to the role, competency, interpretation of question and question? "
        "2. Does it sound like a top performer (great result) or a low performer (lousy result)? "
        "3. List obvious deficiencies without being overly analytical. If the answer is acceptable, move on. "
        "If severely off-topic or weak, suggest a follow-up question."
    )
    messages = [
        {"role": "system", "content": "You are an assessor providing concise, direct feedback. Focus on relevance, performance level, and obvious gaps. Be dry and to the point. No sugarcoating or deep analysis."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7,
        )
        feedback = response.choices[0].message.content.strip()
        return feedback
    except Exception as e:
        return f"Error: {str(e)}"

def get_openai_feedback_and_score(answer_text, guidance):
    messages = [
        {"role": "system", "content": "You are an assistant that evaluates answers based on given guidance. Provide feedback and a score from 1 to 5, where 1 is poor and 5 is excellent, based on how well the answer meets the guidance. (you don't care about spelling errors)"},
        {"role": "user", "content": f"Guidance: {guidance}\n\nAnswer: {answer_text}\n\nProvide feedback and a score (1-5). Format your response as: Feedback: [your feedback]\nScore: [1-5]"}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7,
        )
        result = response.choices[0].message.content.strip()
        feedback = result.split("Score:")[0].replace("Feedback:", "").strip()
        score = int(result.split("Score:")[1].strip())
        return feedback, score
    except Exception as e:
        return f"Error getting feedback: {str(e)}", None

def start_interview(request, competency_id):
    competency = get_object_or_404(Competency, id=competency_id)
    if not competency.gateway_question:
        return render(request, 'error.html', {'message': 'No gateway question set for this competency.'})
    session = InterviewSession.objects.create(
        competency=competency,
        current_question=competency.gateway_question,
        current_category_index=0
    )
    return redirect('interview_question', session_id=session.id)

def department_list(request):
    departments = Department.objects.all()
    return render(request, 'department_list.html', {'departments': departments})

def job_title_list(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    job_titles = JobTitle.objects.filter(department=department)
    return render(request, 'job_title_list.html', {'department': department, 'job_titles': job_titles})

def competency_list(request, job_title_id):
    job_title = get_object_or_404(JobTitle, id=job_title_id)
    competencies = Competency.objects.filter(job_title=job_title)
    if request.method == 'POST':
        selected_competency_ids = request.POST.getlist('competencies')
        if selected_competency_ids:
            request.session['remaining_competencies'] = selected_competency_ids[1:]
            first_competency_id = selected_competency_ids[0]
            return redirect('start_interview', competency_id=first_competency_id)
        else:
            return render(request, 'error.html', {'message': 'Please select at least one competency.'})
    return render(request, 'competency_list.html', {'job_title': job_title, 'competencies': competencies})

def interview_question(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id)
    if session.is_completed:
        return redirect('interview_complete', session_id=session.id)

    if session.current_question:
        question = session.current_question
        if request.method == 'POST':
            answer_text = request.POST.get('answer', '').strip()
            if question.is_scope_question:
                scope_id = request.POST.get('scope_choice')
                if scope_id:
                    chosen_scope = get_object_or_404(Scope, id=scope_id, competency=session.competency)
                    session.chosen_scope = chosen_scope
                    session.current_question = None
                    session.current_category_index = 0
                    session.save()
                    return redirect('interview_question', session_id=session.id)
            else:
                is_yes = request.POST.get('is_yes')
                if answer_text:
                    feedback, score = get_openai_feedback_and_score(answer_text, question.interpretation_guidance)
                    Answer.objects.create(question=question, session=session, text=answer_text, feedback=feedback, score=score)
                if question == session.competency.gateway_question:
                    if is_yes == 'No':
                        session.is_completed = True
                    else:
                        session.current_question = question.next_if_yes
                else:
                    next_question = question.next_if_yes if is_yes == 'Yes' else question.next_if_no
                    if next_question:
                        session.current_question = next_question
                    else:
                        session.is_completed = True
                session.save()
                if session.is_completed:
                    return redirect('interview_complete', session_id=session.id)
                else:
                    return redirect('interview_question', session_id=session.id)
        return render(request, 'interview_question.html', {'question': question, 'session': session})
    else:
        categories = list(session.chosen_scope.categories.all())
        if session.current_category_index < len(categories):
            category = categories[session.current_category_index]
            starting_question = category.starting_question
            if starting_question:
                questions = [starting_question]
                next_q = starting_question.next_if_yes
                while next_q and len(questions) < 3:
                    questions.append(next_q)
                    next_q = next_q.next_if_yes
                if request.method == 'POST':
                    for q in questions:
                        answer_text = request.POST.get(f'answer_{q.id}', '').strip()
                        if answer_text:
                            feedback, score = get_openai_feedback_and_score(answer_text, q.interpretation_guidance)
                            Answer.objects.create(question=q, session=session, text=answer_text, feedback=feedback, score=score)
                    session.current_category_index += 1
                    if session.current_category_index >= len(categories):
                        session.is_completed = True
                    session.save()
                    return redirect('interview_question', session_id=session.id)
                return render(request, 'category_questions.html', {'session': session, 'category': category, 'questions': questions})
            else:
                return render(request, 'error.html', {'message': 'No starting question for this category.'})
        else:
            session.is_completed = True
            session.save()
            return redirect('interview_complete', session_id=session.id)

def interview_complete(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id)
    remaining_competencies = request.session.get('remaining_competencies', [])
    if remaining_competencies:
        next_competency_id = remaining_competencies[0]
        request.session['remaining_competencies'] = remaining_competencies[1:]
        next_competency = get_object_or_404(Competency, id=next_competency_id)
    else:
        next_competency = None
    context = {'session': session, 'next_competency': next_competency}
    return render(request, 'interview_complete.html', context)

def feedback_report(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id)
    answers = Answer.objects.filter(session=session).order_by('created_at')
    feedback_list = [{'question': answer.question.text, 'answer': answer.text, 'feedback': answer.feedback, 'score': answer.score} for answer in answers]
    if feedback_list:
        summary_prompt = "Summarize the candidate's performance based on the following feedback and scores:\n\n"
        for item in feedback_list:
            summary_prompt += f"Question: {item['question']}\nFeedback: {item['feedback']}\nScore: {item['score']}\n\n"
        summary_prompt += "Provide a concise summary of the candidate's overall performance."
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that summarizes candidate performance."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=300,
                temperature=0.7,
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
    else:
        summary = "No answers provided."
    return render(request, 'feedback_report.html', {'feedback_list': feedback_list, 'session_id': session_id, 'summary': summary})