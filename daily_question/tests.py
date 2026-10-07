from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DailyQuestion, QuestionInteraction


class DailyQuestionWallTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

    def create_question(self, question, order):
        return DailyQuestion.objects.create(
            question=question,
            order=order,
            is_active=True,
        )

    def test_first_question_is_displayed(self):
        question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, question.question)

    def test_questions_appear_in_order(self):
        first_question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        second_question = self.create_question(
            "What should we improve?",
            2,
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, first_question.question)
        self.assertNotContains(response, second_question.question)

    def test_no_questions_redirects_to_feed(self):
        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertRedirects(
            response,
            reverse("post_feed"),
        )

    def test_answering_question_creates_interaction(self):
        question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        response = self.client.post(
            reverse("daily_question_wall"),
            {
                "action": "answer",
                "answer": "I would like to see notifications.",
            },
        )

        self.assertRedirects(
            response,
            reverse("post_feed"),
        )

        interaction = QuestionInteraction.objects.get(
            question=question,
            user=self.user,
        )

        self.assertEqual(
            interaction.status,
            QuestionInteraction.ANSWERED,
        )
        self.assertEqual(
            interaction.answer,
            "I would like to see notifications.",
        )

    def test_dismissing_question_creates_interaction(self):
        question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        response = self.client.post(
            reverse("daily_question_wall"),
            {
                "action": "dismiss",
            },
        )

        self.assertRedirects(
            response,
            reverse("post_feed"),
        )

        interaction = QuestionInteraction.objects.get(
            question=question,
            user=self.user,
        )

        self.assertEqual(
            interaction.status,
            QuestionInteraction.DISMISSED,
        )
        self.assertEqual(
            interaction.answer,
            "",
        )

    def test_answered_question_does_not_appear_again(self):
        question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        QuestionInteraction.objects.create(
            question=question,
            user=self.user,
            status=QuestionInteraction.ANSWERED,
            answer="My answer",
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertRedirects(
            response,
            reverse("post_feed"),
        )

    def test_dismissed_question_does_not_appear_again(self):
        question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        QuestionInteraction.objects.create(
            question=question,
            user=self.user,
            status=QuestionInteraction.DISMISSED,
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertRedirects(
            response,
            reverse("post_feed"),
        )

    def test_next_question_appears_after_answering_first(self):
        first_question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        second_question = self.create_question(
            "What should we improve?",
            2,
        )

        self.client.post(
            reverse("daily_question_wall"),
            {
                "action": "answer",
                "answer": "Notifications would be useful.",
            },
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, first_question.question)
        self.assertContains(response, second_question.question)

    def test_next_question_appears_after_dismissing_first(self):
        first_question = self.create_question(
            "What feature would you like to see?",
            1,
        )

        second_question = self.create_question(
            "What should we improve?",
            2,
        )

        self.client.post(
            reverse("daily_question_wall"),
            {
                "action": "dismiss",
            },
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, first_question.question)
        self.assertContains(response, second_question.question)

    def test_inactive_question_is_not_displayed(self):
        self.create_question(
            "Active question",
            1,
        )

        DailyQuestion.objects.create(
            question="Inactive question",
            order=0,
            is_active=False,
        )

        response = self.client.get(
            reverse("daily_question_wall")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active question")
        self.assertNotContains(response, "Inactive question")