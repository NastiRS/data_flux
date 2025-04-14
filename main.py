import asyncio

from agents import RunConfig, Runner
from openai.types.responses import ResponseTextDeltaEvent

from project.core.agents.adder import Adder_Agent
from project.core.agents.analyzer import Analyzer_Agent
from project.core.agents.deleter import Deleter_Agent
from project.core.agents.triage import Triage_Agent
from project.core.agents.updater import Updater_Agent
from project.core.agents_tools.database_tools import (
    database_tables_info,
    delete_a_data,
    find_records,
    find_records_with_complex_conditions,
    get_tokens_count,
    insert_data,
    update_data,
)
from project.core.agents_tools.extra_tools import retrieve_date
from project.core.ai_clients import gpt_4o_model_openai

triage_agent = Triage_Agent(
    handoffs=[], tools=[retrieve_date], model=gpt_4o_model_openai
)

analyzer_agent = Analyzer_Agent(
    handoffs=[],
    tools=[
        retrieve_date,
        database_tables_info,
        find_records,
        find_records_with_complex_conditions,
        get_tokens_count,
    ],
    model=gpt_4o_model_openai,
)

adder_agent = Adder_Agent(
    handoffs=[],
    tools=[
        retrieve_date,
        database_tables_info,
        insert_data,
    ],
    model=gpt_4o_model_openai,
)

deleter_agent = Deleter_Agent(
    handoffs=[],
    tools=[
        retrieve_date,
        database_tables_info,
        find_records,
        find_records_with_complex_conditions,
        delete_a_data,
    ],
    model=gpt_4o_model_openai,
)

updater_agent = Updater_Agent(
    handoffs=[],
    tools=[
        retrieve_date,
        database_tables_info,
        update_data,
        find_records,
        find_records_with_complex_conditions,
    ],
    model=gpt_4o_model_openai,
)

triage_agent.handoffs = [analyzer_agent, adder_agent, deleter_agent, updater_agent]
analyzer_agent.handoffs = [triage_agent, adder_agent, deleter_agent, updater_agent]
adder_agent.handoffs = [triage_agent, analyzer_agent, deleter_agent, updater_agent]
deleter_agent.handoffs = [triage_agent, analyzer_agent, adder_agent, updater_agent]
updater_agent.handoffs = [triage_agent, analyzer_agent, adder_agent, deleter_agent]

config = RunConfig(tracing_disabled=True)


async def call_streaming():
    result = Runner.run_streamed(
        analyzer_agent,
        input="Hay alguna venta que haya hecho el empleado Carlos Lara?el 2 de enero del 2025.",
    )
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            print(event.data.delta, end="", flush=True)


print(asyncio.run(call_streaming()))
