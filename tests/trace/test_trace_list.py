import pytest
from macq.trace import TraceList
from tests.utils.generators import (
    generate_test_trace_list,
    generate_test_trace,
    generate_blocks_traces,
)

MissingGenerator = TraceList.MissingGenerator


def test_trace_list():
    trace_list = generate_test_trace_list(5)

    assert len(trace_list) == 5

    with pytest.raises(MissingGenerator):
        trace_list.generate_more(5)

    first = trace_list[0]
    trace_list.generator = generate_test_trace
    assert trace_list[0] is first

    action = trace_list[0].steps[0].action
    assert action
    usages = trace_list.get_usage(action)
    for i, trace in enumerate(trace_list):
        assert usages[i] == trace.get_usage(action)

    trace = generate_test_trace()
    trace_list[0] = trace
    assert trace_list[0] is trace
    del trace_list[0]
    assert trace_list[0] != trace
    assert list(reversed(trace_list))[0] == trace_list[-1]
    trace_list.clear()
    assert len(trace_list) == 0

    traces = [generate_test_trace() for _ in range(5)]
    trace_list.extend(traces)

    trace_list.insert(0, trace)
    assert trace in trace_list
    assert trace_list.index(trace) == 0

    trace_list.pop()
    assert len(trace_list) == 5

    trace_list.reverse()
    assert trace_list[-1] == trace
    trace_list.remove(trace)
    assert trace not in trace_list

    assert trace_list.traces == trace_list.copy()

    trace_list.sort()
    trace_list.print()
