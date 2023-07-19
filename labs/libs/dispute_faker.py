from datetime import datetime
from pprint import pprint

import bson
from faker import Factory, Faker, Generator, providers, utils
from faker.providers import currency, date_time, file


fake = Faker(use_weighting=True)
fake.add_provider(currency)
fake.add_provider(date_time)

FILE_CATEGORY = ["video", "image", "text"]
PROPOSED_SOLUTION = [
    "FULL_REFUND",
    "PARTIAL_REFUND",
    "REPLACE_ITEM",
    "RETURN_AND_REFUND",
    "SHIP_MISSING_QUANTITY",
    "SHIP_NEW_ITEM",
]
PROPOSAL_STATUS = ["COUNTERED", "ACCEPTED", "PENDING_DECISION"]
RESOLUTION_STATUS = ["ARBITRATED", "WAITING_FOR_ARBITRATION", "ESCALATED"]
DISPUTE_REASON = [
    "ITEM_NOT_MATCH_DESCRIPTION",
    "MISSING_QUANTITY",
    "DAMAGED",
    "WRONG_ITEM",
    "ITEM_NOT_RECEIVED",
    "OTHER",
]
HALF_HOUR = 1800
THREE_DAYS = 259200
pass


def generate_item():
    item_id = str(fake.numerify(text="##"))
    item = {
        "itemPrice": {
            "cent": fake.pyint(min_value=100, max_value=100000000),
            "currency": fake.currency_code(),
        },
        "supportFreeReturn": fake.pybool(),
        "itemCount": fake.pyint(min_value=1, max_value=50),
        "itemId": item_id,
        "skuId": str(fake.numerify(text="##")),
        "skuValue": fake.pystr(min_chars=1, max_chars=8),
        "tradeSnapshotUrl": f"https://jailed-market.com/product/{item_id}/details?snapshot={fake.date_between(start_date='-30d', end_date='today')}",
        "ParentOrderId": str(fake.numerify(text="##")),
    }
    return item


def generate_attachment():
    file_type = fake.random_element(elements=FILE_CATEGORY)
    attachment = {
        "artifactId": fake.uuid4(),
        "mimeType": fake.mime_type(category=file_type),
        "extFileName": fake.file_name(category=file_type, extension=None),
        "description": fake.sentence(
            nb_words=6, variable_nb_words=True, ext_word_list=None
        ),
    }
    return attachment


def generate_attachments():
    attachments = []
    for _ in range(fake.pyint(min_value=0, max_value=3)):
        attachments.append(generate_attachment())
    return attachments


def generate_resolution_proposal(base_time=0):
    proposal = {
        "gmtSubmitted": base_time + fake.pyint(min_value=HALF_HOUR, max_value=THREE_DAYS),
        "richTextReport": fake.sentence(nb_words=18, variable_nb_words=True, ext_word_list=None),
        "proposedSolution": fake.random_element(elements=PROPOSED_SOLUTION),
        "status": fake.random_element(elements=PROPOSAL_STATUS),
        "attachments": generate_attachments(),
    }
    return proposal


def generate_resolution_round(base_time=0):
    initial_proposal = generate_resolution_proposal(base_time)
    base_time = initial_proposal["gmtSubmitted"]

    resolution_round = {
        "initialProposal": initial_proposal,
    }

    if initial_proposal["status"] in ["PENDING_DECISION", "ACCEPTED"]:
        resolution_round["counterProposal"] = None

    if initial_proposal["status"] == "COUNTERED":
        resolution_round["counterProposal"] = generate_resolution_proposal(base_time)

    return resolution_round


def generate_resolution(base_time=0):
    first_round = generate_resolution_round(base_time)
    fr_initial_proposal = first_round["initialProposal"]
    fr_initial_proposal_status = fr_initial_proposal["status"]

    resolution = {
        "status": None,
        "arbitratorId": None,
        "gmtArbitratorAssigned": None,
        "gmtArbitrated": None,
        "decision": None,
        "firstRound": first_round,
        "lastRound": None,
    }

    if fr_initial_proposal_status == "PENDING_DECISION":
        resolution["status"] = "WAITING_FOR_SELLER"
        last_updated_time = fr_initial_proposal["gmtSubmitted"]
        return resolution, last_updated_time

    if fr_initial_proposal_status == "ACCEPTED":
        resolution["status"] = "REACHED_AGREEMENT"
        resolution["decision"] = fr_initial_proposal["proposedSolution"]
        last_updated_time = fr_initial_proposal["gmtSubmitted"]
        return resolution, last_updated_time

    fr_counter_proposal = first_round.get("counterProposal")
    fr_counter_proposal_status = fr_counter_proposal.get("status")

    if (
        fr_initial_proposal_status == "COUNTERED"
        and fr_counter_proposal_status == "PENDING_DECISION"
    ):
        resolution["status"] = "WAITING_FOR_BUYER"
        last_updated_time = fr_counter_proposal["gmtSubmitted"]

    if (
        fr_initial_proposal_status == "COUNTERED"
        and fr_counter_proposal_status == "ACCEPTED"
    ):
        resolution["status"] = "REACHED_AGREEMENT"
        resolution["decision"] = fr_counter_proposal["proposedSolution"]
        last_updated_time = fr_counter_proposal["gmtSubmitted"]

    if (
        fr_initial_proposal_status == "COUNTERED"
        and fr_counter_proposal_status == "COUNTERED"
    ):
        last_round = generate_resolution_round(fr_counter_proposal["gmtSubmitted"])

        lr_initial_proposal = last_round["initialProposal"]
        lr_initial_proposal_status = lr_initial_proposal["status"]

        lr_counter_proposal = first_round.get("counterProposal", {})
        lr_counter_proposal_status = lr_counter_proposal.get("status", None)

        resolution["lastRound"] = last_round

        if lr_initial_proposal_status == "PENDING_DECISION":
            resolution["status"] = "WAITING_FOR_SELLER"
            last_updated_time = lr_initial_proposal["gmtSubmitted"]

        if lr_initial_proposal_status == "ACCEPTED":
            resolution["status"] = "REACHED_AGREEMENT"
            resolution["decision"] = lr_initial_proposal["proposedSolution"]
            last_updated_time = lr_initial_proposal["gmtSubmitted"]

        if (
            lr_initial_proposal_status == "COUNTERED"
            and lr_counter_proposal_status == "PENDING_DECISION"
        ):
            resolution["status"] = "WAITING_FOR_BUYER"
            last_updated_time = lr_counter_proposal["gmtSubmitted"]

        if (
            lr_initial_proposal_status == "COUNTERED"
            and lr_counter_proposal_status == "ACCEPTED"
        ):
            resolution["status"] = "REACHED_AGREEMENT"
            resolution["decision"] = lr_counter_proposal["proposedSolution"]
            last_updated_time = lr_counter_proposal["gmtSubmitted"]

        if (
            lr_initial_proposal_status == "COUNTERED"
            and lr_counter_proposal_status == "COUNTERED"
        ):
            resolution["lastRound"]["counterProposal"]["status"] = "REJECTED"
            resolution["status"] = fake.random_element(elements=RESOLUTION_STATUS)
            last_updated_time = lr_counter_proposal["gmtSubmitted"]

            if resolution["status"] == "WAITING_FOR_ARBITRATION":
                resolution["arbitratorId"] = str(fake.numerify(text="#"))
                last_updated_time = last_updated_time + fake.pyint(
                    min_value=HALF_HOUR / 6, max_value=THREE_DAYS / 3
                )
                resolution["gmtArbitratorAssigned"] = last_updated_time

            if resolution["status"] == "ARBITRATED":
                resolution["arbitratorId"] = str(fake.numerify(text="#"))
                last_updated_time = last_updated_time + fake.pyint(
                    min_value=HALF_HOUR / 6, max_value=THREE_DAYS / 3
                )
                resolution["gmtArbitratorAssigned"] = last_updated_time
                last_updated_time = last_updated_time + fake.pyint(
                    min_value=HALF_HOUR / 6, max_value=THREE_DAYS / 3
                )
                resolution["gmtArbitrated"] = last_updated_time
                resolution["decision"] = fake.random_element(elements=PROPOSED_SOLUTION)

            resolution["decision"] = lr_counter_proposal["proposedSolution"]

    return (resolution, last_updated_time)


def generate_dispute():
    create_time = fake.unix_time(
        end_datetime=datetime.now(), start_datetime=datetime.fromisoformat("2020-01-01")
    )
    resolution, last_updated_time = generate_resolution(create_time)
    dispute = {
        "_id": bson.ObjectId(),
        "disputeReason": fake.random_element(elements=DISPUTE_REASON),
        "buyerId": str(fake.numerify(text="##")),
        "gmtCreated": create_time,
        "gmtModified": last_updated_time,
        "sellerId": str(fake.numerify(text="##")),
        "item": generate_item(),
        "resolution": resolution,
    }
    return dispute


if __name__ == "__main__":
    for _ in range(1):
        reso = generate_dispute()
        pprint(reso)
