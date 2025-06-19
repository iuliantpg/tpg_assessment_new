from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class JobTitle(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    summary = models.TextField(blank=True, help_text="Summary of what this role usually does.")
    history = models.TextField(blank=True, help_text="Brief history of the role.")

    def __str__(self):
        return self.title

class Competency(models.Model):
    job_title = models.ForeignKey(JobTitle, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Brief description of what this competency entails.")
    gateway_question = models.ForeignKey('Question', null=True, blank=True, on_delete=models.SET_NULL, related_name='competency_gateway')
    scope_question = models.ForeignKey('Question', null=True, blank=True, on_delete=models.SET_NULL, related_name='competency_scope')

    def __str__(self):
        return f"{self.job_title.title} - {self.name}"

class Category(models.Model):
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    starting_question = models.ForeignKey('Question', null=True, blank=True, on_delete=models.SET_NULL, related_name='category_start')

    def __str__(self):
        return f"{self.competency.name} - {self.name}"

class Scope(models.Model):
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(Category)

    def __str__(self):
        return f"{self.competency.name} - {self.name}"

class Question(models.Model):
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    sophistication_level = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    is_scope_question = models.BooleanField(default=False)
    next_if_yes = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='yes_followups')
    next_if_no = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='no_followups')
    interpretation_guidance = models.TextField(blank=True, help_text="Guidance on how to interpret the answer.")

    def __str__(self):
        return self.text

class InterviewSession(models.Model):
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    current_question = models.ForeignKey(Question, null=True, blank=True, on_delete=models.SET_NULL)
    chosen_scope = models.ForeignKey(Scope, null=True, blank=True, on_delete=models.SET_NULL)
    selected_competencies = models.ManyToManyField(Competency, related_name='sessions', blank=True)
    current_category_index = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    text = models.TextField()
    feedback = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)