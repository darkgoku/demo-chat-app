import multiprocessing
import os
import signal
import sys
import time

import pytest
from pytest_cov.embed import cleanup_on_sigterm

from app.wsgi import http_server


@pytest.fixture(scope="module")
def server():
    """Run the flask server for the duration of tests in this module."""
    cleanup_on_sigterm()
    p = multiprocessing.Process(target=http_server.serve_forever)
    p.start()
    yield p

    p.terminate()

    print("Waiting for process to terminate.")
    for i in range(10):
        if not p.is_alive():
            print("    ... process is dead.")
            break
        time.sleep(0.2)
        print("    ... waiting")

    p.join()
    p.close()


@pytest.fixture
def chrome_options(request, chrome_options):
    chrome_options.add_argument("--headless")
    return chrome_options


def test_one_user_joining_room_sending_message(selenium, server):
    selenium.implicitly_wait(10)  # seconds

    # get into a room
    selenium.get("http://0.0.0.0:5000/")
    selenium.find_element_by_name("username").send_keys("dark")
    selenium.find_element_by_name("code").send_keys("goku")
    selenium.find_element_by_tag_name("form").submit()

    # assertions about the room
    assert "<h1>Room: goku</h1>" in selenium.page_source

    # send a message and check it comes back
    selenium.find_element_by_name("message").send_keys("hi paris what is up")
    selenium.find_element_by_tag_name("form").submit()
    time.sleep(0.05)
    assert "hi paris what is up" in selenium.page_source
