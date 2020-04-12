import multiprocessing
import time

import pytest
from pytest_cov.embed import cleanup_on_sigterm

from app.wsgi import http_server


@pytest.fixture
def chrome_options(request, chrome_options):
    """Headless option for selenium fixture."""
    chrome_options.add_argument("--headless")
    return chrome_options


def join_a_room(selenium, username: str, code: str, implicit_wait: float = 10.0):
    """Helper to put selenium in a room. 
    
    Returns a mutate browser state after having validated the room header.
    """
    selenium.implicitly_wait(implicit_wait)
    selenium.get("http://0.0.0.0:5000/")
    selenium.find_element_by_name("username").send_keys(username)
    selenium.find_element_by_name("code").send_keys(code)
    selenium.find_element_by_tag_name("form").submit()

    # assertions about the room
    assert f"<h1>Room: {code}</h1>" in selenium.page_source
    return selenium


def send_a_message(selenium, message: str, implicit_wait: float = 10.0):
    """Helper to send a message. 
    
    Returns a mutated browser state after having validated the message was sent. 
    Assumes /room is entered.
    """
    selenium.implicitly_wait(implicit_wait)
    selenium.find_element_by_name("message").send_keys(message)
    selenium.find_element_by_tag_name("form").submit()
    time.sleep(0.05)
    assert message in selenium.page_source
    return selenium


def join_a_room_send_a_message(
    selenium, username: str, code: str, message: str, implicit_wait: float = 10.0
):
    """Nested combination of join and room and send a message."""
    return send_a_message(
        join_a_room(selenium, username, code, implicit_wait=implicit_wait),
        message,
        implicit_wait=implicit_wait,
    )


@pytest.fixture(scope="module")
def server():
    """Run the flask server for the duration of tests in this module."""
    cleanup_on_sigterm()
    p = multiprocessing.Process(target=http_server.serve_forever)
    p.start()
    yield p

    p.terminate()

    print("\nWaiting for process to terminate.")
    for i in range(10):
        if not p.is_alive():
            print("    ... process is dead.")
            break
        time.sleep(0.2)
        print("    ... waiting")
    print()

    p.join()
    p.close()


def test_one_user_joining_room_sending_message(selenium, server):
    join_a_room_send_a_message(selenium, "dark", "goku", "hi paris what is up")


def test_one_user_switching_rooms(selenium, server):
    selenium = join_a_room_send_a_message(
        selenium, "user_1", "room_1", "I am user 1 in room 1."
    )
    selenium = join_a_room_send_a_message(
        selenium, "user_2", "room_2", "I am user 2 in room 2."
    )

    # check room 1 stuff is not in room 2
    assert "<h1>Room: room_1</h1>" not in selenium.page_source
    assert "I am user 1 in room 1." not in selenium.page_source

    # rejoin room 1 and check room 2 stuff is not there
    selenium = join_a_room(selenium, "user_1", "room_1")
    assert "<h1>Room: room_2</h1>" not in selenium.page_source
    assert "I am user 2 in room 2." not in selenium.page_source
