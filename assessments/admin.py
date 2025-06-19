from django.contrib import admin
from .models import Department, JobTitle, Competency, Category, Scope, Question, Answer, InterviewSession

class JobTitleAdmin(admin.ModelAdmin):
    list_display = ['title', 'department']
    fields = ['department', 'title', 'summary', 'history']

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'competency', 'category', 'sophistication_level', 'is_scope_question']
    fields = ['competency', 'category', 'text', 'sophistication_level', 'is_scope_question', 'next_if_yes', 'next_if_no', 'interpretation_guidance']

class CompetencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_title']
    fields = ['job_title', 'name', 'description', 'gateway_question', 'scope_question']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'competency']
    fields = ['competency', 'name', 'starting_question']

class ScopeAdmin(admin.ModelAdmin):
    list_display = ['name', 'competency']
    fields = ['competency', 'name', 'categories']
    filter_horizontal = ['categories']

admin.site.register(Department)
admin.site.register(JobTitle, JobTitleAdmin)
admin.site.register(Competency, CompetencyAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Scope, ScopeAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(InterviewSession)