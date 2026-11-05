import os
import sys
from datetime import date, datetime

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_assistant_flow_in_streamlit():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30).run()
    assert not at.exception

    owner = at.session_state["owner"]
    from pawpal.models import Pet, Task

    pet = Pet("Rex", "dog")
    owner.add_pet(pet)
    today = date.today()
    pet.add_task(Task("Walk", 30, 2, "Rex", time=datetime.combine(today, datetime.min.time()).replace(hour=8)))
    pet.add_task(Task("Groom", 30, 2, "Rex", time=datetime.combine(today, datetime.min.time()).replace(hour=8, minute=15)))
    at.run()

    next(b for b in at.button if b.label == "Start planning").click().run()
    assert not at.exception
    assert any("Conflict" in w.value for w in at.warning)

    next(b for b in at.button if b.label == "Apply my choice").click().run()
    assert not at.exception
    assert any(b.label == "Approve and save plan" for b in at.button)

    next(b for b in at.button if b.label == "Approve and save plan").click().run()
    assert not at.exception
    assert any("approved and saved" in s.value for s in at.success)
