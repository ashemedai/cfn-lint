"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from collections import deque

import pytest

from cfnlint.context import Path, create_context_for_template
from cfnlint.helpers import FUNCTIONS
from cfnlint.jsonschema import CfnTemplateValidator, ValidationError

# ruff: noqa: E501
from cfnlint.rules.resources.RetentionPeriodOnResourceTypesWithAutoExpiringContent import (
    RetentionPeriodOnResourceTypesWithAutoExpiringContent,
)
from cfnlint.template import Template


@pytest.fixture(scope="module")
def rule():
    rule = RetentionPeriodOnResourceTypesWithAutoExpiringContent()
    yield rule


@pytest.fixture(scope="module")
def validator():
    cfn = Template(
        "",
        {
            "Resources": {
                "MySqs": {
                    "Type": "AWS::SQS::Queue",
                }
            }
        },
    )
    context = create_context_for_template(cfn).evolve(
        functions=FUNCTIONS,
        path=Path(
            path=deque(["Resources", "MySqs", "Properties"]),
            cfn_path=deque(["Resources", "AWS::SQS::Queue", "Properties"]),
        ),
    )
    yield CfnTemplateValidator(schema={}, context=context, cfn=cfn)


@pytest.mark.parametrize(
    "name,instance,expected",
    [
        (
            "Valid version",
            {"MessageRetentionPeriod": "90"},
            [],
        ),
        (
            "Invalid type",
            [],
            [],
        ),
        (
            "Invalid when not specified",
            {},
            [
                ValidationError(
                    (
                        "'MessageRetentionPeriod' is a required property (The "
                        "default retention period will delete the data after "
                        "a pre-defined time. Set an explicit values to avoid "
                        "data loss on resource)"
                    ),
                    rule=RetentionPeriodOnResourceTypesWithAutoExpiringContent(),
                    schema_path=deque(["required"]),
                    validator="required",
                    validator_value=["MessageRetentionPeriod"],
                    instance={},
                )
            ],
        ),
    ],
)
def test_validate(name, instance, expected, rule, validator):
    errors = list(rule.validate(validator, False, instance, {}))
    # we use error counts in this one as the instance types are
    # always changing so we aren't going to hold ourselves up by that
    assert errors == expected, f"Test {name!r} got {errors!r}"


def test_validate_with_no_path(rule, validator):
    validator = validator.evolve(
        context=validator.context.path.evolve(
            path=Path(path=deque([]), cfn_path=deque([]))
        )
    )

    errors = list(rule.validate(validator, False, {}, {}))
    assert errors == []
