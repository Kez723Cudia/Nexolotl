from django import forms

from .models import QuestionInteraction


class DailyQuestionForm(forms.ModelForm):
    class Meta:
        model = QuestionInteraction
        fields = ["answer"]
        widgets = {
            "answer": forms.Textarea(
                attrs={
                    "placeholder": "Write your answer here...",
                    "rows": 5,
                }
            ),
        }

    def clean_answer(self):
        answer = self.cleaned_data["answer"].strip()

        if not answer:
            raise forms.ValidationError("Please enter an answer.")

        return answer