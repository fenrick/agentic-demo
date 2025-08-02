import pytest
from app.agents import PedagogyCritic, QAReviewer


@pytest.mark.xfail(reason="PedagogyCritic not implemented")
def test_pedagogy_critic_placeholder():
    critic = PedagogyCritic()
    critic("test input")


@pytest.mark.xfail(reason="QAReviewer not implemented")
def test_qa_reviewer_placeholder():
    reviewer = QAReviewer()
    reviewer("draft text")
