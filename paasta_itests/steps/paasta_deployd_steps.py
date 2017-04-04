from __future__ import absolute_import
from __future__ import unicode_literals

import errno
import os
import time

from behave import given
from behave import then

from paasta_tools.deployd.master import DeployDaemon
from paasta_tools.marathon_tools import list_all_marathon_app_ids
from paasta_tools.marathon_tools import load_marathon_service_config
from paasta_tools.utils import decompose_job_id


@given('paasta-deployd is running')
def start_deployd(context):
    try:
        os.makedirs('/nail/etc/services')
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
    context.soa_dir = '/nail/etc/services'
    if not hasattr(context, 'daemon'):
        context.daemon = DeployDaemon()
        context.daemon.start()
    for i in range(0, 10):
        if context.daemon.started:
            return
        time.sleep(3)
    assert context.daemon.started


@then('paasta-deployd can be stopped')
def stop_deployd(context):
    context.daemon.stop()
    for i in range(0, 5):
        if not context.daemon.is_alive():
            return
        time.sleep(3)
    assert not context.daemon.is_alive()


@then('a second deployd does not become leader')
def start_second_deployd(context):
    context.daemon1 = DeployDaemon()
    context.daemon1.start()
    for i in range(0, 5):
        if hasattr(context.daemon1, 'is_leader'):
            break
        time.sleep(1)
    time.sleep(1)
    assert not context.daemon1.is_leader


@then('a second deployd becomes leader')
def second_deployd_is_leader(context):
    for i in range(0, 5):
        if context.daemon1.started:
            break
        time.sleep(3)
    assert context.daemon1.started
    context.daemon1.stop()
    for i in range(0, 5):
        if not context.daemon1.is_alive():
            break
        time.sleep(3)
    assert not context.daemon1.is_alive()
    assert not context.daemon.is_alive()


@then('we should see "{service_instance}" listed in marathon after {seconds:d} seconds')
def check_app_running(context, service_instance, seconds):
    service, instance, _, _ = decompose_job_id(service_instance)
    context.marathon_config = load_marathon_service_config(service, instance, context.cluster)
    context.app_id = context.marathon_config.format_marathon_app_dict()['id']
    step = 5
    attempts = 0
    while (attempts * step) < seconds:
        if context.app_id in list_all_marathon_app_ids(context.marathon_client):
            return
        time.sleep(step)
        attempts += 1
    assert context.app_id in list_all_marathon_app_ids(context.marathon_client)
