#!/usr/bin/env python3
#
""" TODO: missing module docstring

"""

import json
import argh
from actions import ActionContext, Action


class JSON(Action):
    def run(self, actions):
        info = []
        for action in actions:
            action(None)
            info.append(action.stats)
        return [json.dumps(info, indent=4)]


class CSV(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

        self._printheader = self._params['printheader']
        self._onlyheader = self._params['onlyheader']
        self._repeatheader = self._params['repeatheader']

        self._csvkeys = []

    def init_keys(self, actions):

        # find csv keys
        keys = set()
        for a in actions:
            keys |= set(a.get_stat_keys())
        self._csvkeys = sorted(keys)

    def header(self):
        return ",".join(self._csvkeys)

    def csvline(self, action: Action):
        values = []
        for key in self._csvkeys:
            val = action.get_stat(key, "")
            values.append(str(val))
        return ",".join(values)

    def run(self, actions):
        if self._printheader:
            yield self.header()
            if not self._repeatheader:
                self._printheader = False
        if not self._onlyheader:
            for action in actions:
                action(None)
                yield self.csvline(action)

    @staticmethod
    def default_params():
        return {
            'printheader': False,
            'onlyheader': False,
            'repeatheader': False,
        }


class Output(Action):
    def __init__(self, context, parents, params):
        super().__init__(context, parents, params)

        # how to print (options: 'csv', 'json')
        self._printer = self._params['printer']
        if self._printer not in ['csv', 'json']:
            raise Exception(f"{self._printer} is not a valid option for 'printer'")

    def run(self, actions):

        if self._printer == 'json':
            printer = self.retrieve_action("JSON")
        else:  # self._printer == 'csv':
            printer = self.retrieve_action("CSV")
            printer.init_keys(actions)
        return printer

    @staticmethod
    def default_params():
        return {
            'printer': 'csv',
        }


class Runner:
    """TODO

    """

    def __init__(self, action_name, *actions):
        self._action_name = action_name
        self._actions = actions

    def _get_context(self, filters):
        context = ActionContext()
        context.register_actions(*self._actions)
        context.register_actions(Output)
        context.register_actions(JSON)
        context.register_actions(CSV)
        context.register_filters(*filters)
        return context

    def _get_printer(self, context: ActionContext):
        output_action = context.construct_action(Output.name())

        ctx_no_filter = ActionContext(use_defaults=False)
        ctx_no_filter.register_actions(*self._actions)
        actions = ctx_no_filter.construct_variants(self._action_name)

        return output_action(actions)


    @argh.arg('-f', '--filters', nargs='+', action='extend')
    def run(self, filters=[]):
        context = self._get_context(filters)

        printer = self._get_printer(context)

        action = context.construct_action(self._action_name)
        output = printer([action])
        return output

    @argh.arg('-f', '--filters', nargs='+', action='extend')
    def run_all(self, filters=[], all_variants=False):
        use_defaults = not all_variants
        context = self._get_context(filters)
        context.use_defaults = use_defaults

        printer = self._get_printer(context)

        actions = context.construct_variants(self._action_name)
        for line in printer(actions):
            yield line


    @argh.arg('-f', '--filters', nargs='+', action='extend')
    def print(self, filters=[]):
        context = self._get_context(filters)

        action = context.construct_action(self._action_name)
        print(action)

    @argh.arg('-f', '--filters', nargs='+', action='extend')
    def print_all(self, filters=[], all_variants=False):
        use_defaults = not all_variants
        context = self._get_context(filters)
        context.use_defaults = use_defaults

        actions = context.construct_variants(self._action_name)
        for action in actions:
            print(action)
