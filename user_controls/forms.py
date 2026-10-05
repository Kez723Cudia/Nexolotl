from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    def __init__(
        self,
        *args,
        reporter=None,
        reported_user=None,
        reported_post=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.reporter = reporter
        self.reported_user = reported_user
        self.reported_post = reported_post

    class Meta:
        model = Report
        fields = ["reason", "description"]

        widgets = {
            "reason": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Provide more details (optional)..."
                    ),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        has_user = self.reported_user is not None
        has_post = self.reported_post is not None

        if has_user == has_post:
            raise forms.ValidationError(
                "A report must target exactly one account or one post."
            )

        if self.reporter is not None:
            if has_user and self.reported_user == self.reporter:
                raise forms.ValidationError(
                    "You cannot report your own account."
                )

            if has_post and self.reported_post.author == self.reporter:
                raise forms.ValidationError(
                    "You cannot report your own post."
                )

            duplicate_filter = {
                "reporter": self.reporter,
            }

            if has_user:
                duplicate_filter["reported_user"] = self.reported_user
            else:
                duplicate_filter["reported_post"] = self.reported_post

            if Report.objects.filter(**duplicate_filter).exists():
                raise forms.ValidationError(
                    "You have already reported this target."
                )

        return cleaned_data