from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import DailyQuestionForm
from .models import DailyQuestion, QuestionInteraction


@login_required
def daily_question_wall(request):
    question = (
        DailyQuestion.objects
        .filter(is_active=True)
        .exclude(interactions__user=request.user)
        .first()
    )

    # If there are no more questions, go directly to the feed.
    if question is None:
        return redirect("post_feed")

    if request.method == "POST":
        action = request.POST.get("action")

        # Dismiss the question.
        if action == "dismiss":
            QuestionInteraction.objects.create(
                question=question,
                user=request.user,
                status=QuestionInteraction.DISMISSED,
            )
            return redirect("post_feed")

        # Answer the question.
        if action == "answer":
            form = DailyQuestionForm(request.POST)

            if form.is_valid():
                interaction = form.save(commit=False)
                interaction.question = question
                interaction.user = request.user
                interaction.status = QuestionInteraction.ANSWERED
                interaction.save()

                return redirect("post_feed")
        else:
            form = DailyQuestionForm()
    else:
        form = DailyQuestionForm()

    return render(
        request,
        "daily_question/daily_question_wall.html",
        {
            "question": question,
            "form": form,
        },
    )