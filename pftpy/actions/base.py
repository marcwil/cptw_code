#!/usr/bin/env python3
"""
TODO-List:
* write documentation
* DONE ActionContext
** DONE base functionality
*** DONE filter stuff (most specific filter and choice)
*** DONE run all, print all, …
** DONE CLI
** DONE CSV-Printing
** DONE Verbose-Printing
* DONE Action.__call__(): fix multiplicity of input
* DONE Action.run parameters
* DONE Printers as Actions
* STRT unit tests
* DONE stats: add possibility to compute stats outside run (to not affect timing)
* DONE get_stat_keys should be static I guess? -> NOPE
* TODO refactor subprocess IO into actions/util.py
* TODO fix: run-all only produces one action even if multiple results for
       retrieve_action are available
* TODO error handling / timeout handling
** TODO allowed exceptions vs disallowed ones
* DONE more abstractions around _stats: forbid adding undefined keys
"""

from abc import ABC, abstractmethod
import itertools
import datetime


class ActionContext(ABC):
    """
    TODO

    """
    def __init__(self, use_defaults=True):
        self._filters = []
        self._actions = {}
        """dict: str -> Action"""

        self._use_defaults = use_defaults  # todo should this be a mutable property?

# ?
#    @property
#    def filters(self):
#        return self._filters
#
#    @property
#    def actions(self):
#        return self._actions

    @property
    def use_defaults(self):
        """TODO"""
        return self._use_defaults

    @use_defaults.setter
    def use_defaults(self, value):
        """TODO"""
        self._use_defaults = value


    def register_filters(self, *filters):
        """TODO"""
        self._filters += filters

    def register_actions(self, *actions):
        """TODO"""
        for action in actions:
            name = action.name()
            # make sure action of same name has not been registered before
            assert name not in self._actions, f"{name} was already registered"
            self._actions[action.name()] = action

    @staticmethod
    def _match_specificity(filter_str: str, call_stack: 'list[str]'):
        """Returns the number of matches between call stack and filter
        specification or 0 if they don't match.

        Example:
        _match_specificity(["a"], ["a"]) == 1
        _match_specificity(["a"], ["b"]) == 0
        _match_specificity(["d"], ["a:b:c:d"]) == 1
        _match_specificity(["c:d"], ["a:b:c:d"]) == 2
        _match_specificity(["a:c:d"], ["a:b:c:d"]) == 0
        """
        filter_split = filter_str.split(":")
        filter_split.reverse()
        if "(" in filter_split[0]:
            filter_split[0] = filter_split[0].split("(")[0]

        num_match = 0
        for fname, sname in zip(filter_split, reversed(call_stack)):
            if fname == sname:
                num_match += 1
            else:
                num_match = 0
                break
        return num_match

    def most_specific_filters(self, parents, action_name):
        """TODO

        """
        call_stack = parents + [action_name]

        most_specific = []
        highest_specificity = 1
        for filter in self._filters:
            specificity = self._match_specificity(filter, call_stack)
            # higher specificity: begin new list
            if specificity > highest_specificity:
                highest_specificity = specificity
                most_specific = []
            # high specificity: add to current list
            if specificity == highest_specificity:
                most_specific.append(filter)
        # return stuff
        return most_specific

    def most_specific_choice(self, parents, choice_action_name):
        call_stack = parents + [choice_action_name]

        most_specific = []
        highest_specificity = 1
        for filter in self._filters:
            truncated = filter.split(":")[:-1]
            truncated = ":".join(truncated)
            if len(truncated) == 0:
                continue
            specificity = self._match_specificity(truncated, call_stack)
            # higher specificity: begin new list
            if specificity > highest_specificity:
                highest_specificity = specificity
                most_specific = []
            # high specificity: add to current list
            if specificity == highest_specificity:
                most_specific.append(filter)
        return most_specific

    def construct_action(self, name, parents=None):
        """TODO: write docstring"""
        action = self._actions[name]
        if parents is None:
            parents = []
        return action.construct(self, parents)

    def construct_variants(self, name, parents=None):
        """TODO"""
        action = self._actions[name]
        if parents is None:
            parents = []
        return action.construct_all(self, parents)


class BadStatKeyError(LookupError):
    pass


class Action():

    def __init__(self, context: ActionContext, parents=None, parameters=None):
        self._stats = {}
        self._context: ActionContext = context

        if parents is None:
            parents = []
        self._call_stack = parents + [self.name()]

        self._params = self.default_params()
        if parameters is not None:
            self._params.update(parameters)

    def __call__(self, input):
        t0 = datetime.datetime.now()
        try:
            ret = self.run(input)
            t1 = datetime.datetime.now()
            if 'error_status' not in self._stats:
                self.set_stat('error_status', 'none')
            self.compute_stats(input, ret)
        except BadStatKeyError as e:
            raise(e)
        except Exception as e:
            ret = None
            t1 = datetime.datetime.now()
            self.set_stat('error_status', f"exception({e})")
        finally:
            delta = t1 - t0
            self.set_stat('time', delta.total_seconds())

        return ret

    @abstractmethod
    def run(self, input):
        """Overwrite this function to define a custom action instead of
        assigning a callable to the action variable
        TODO: do we really need to pass parameters here?
        """
        raise NotImplementedError()

    @staticmethod
    def default_params():
        return {}

    @classmethod
    def name(cls) -> 'str':
        """Returns the name of the Action, which should be unique in the Actions
        ActionContext

        """
        return cls.__name__

    def set_stat(self, key, value):
        if key in self.get_stat_keys():
            self._stats[key] = value
        else:
            raise BadStatKeyError(f"{key} not defined as stat key in {self}")

    def get_stat(self, key, default=None):
        if default is None:
            return self._stats.get(key)
        else:
            return self._stats.get(key, default)

    @property
    def stats(self) -> 'dict[str,str]':
        return self._stats

    def compute_stats(self, input, output):
        """
        Override this function in order to compute stats after the call of `run`.
        This is useful for computations of stats that are expensive and would influence the timing.
        """
        pass

    def get_stat_keys(self) -> 'list[str]':
        return ['time', 'error_status']

    def retrieve_action(self, action_name: str) -> 'Action':
        """
        Use this action to obtain an action (via `construct_action`) from this Action's ActionContext.
        """
        return self._context.construct_action(action_name, self._call_stack)

    def retrieve_variants(self, action_name: str) -> 'list[Action]':
        """
        Use this action to obtain an action (via `construct_variants`) from this Action's ActionContext.
        """
        return self._context.construct_variants(action_name, self._call_stack)


    @staticmethod
    def parse_parameters(filters):
        res = []
        for f in filters:
            last = f.split(":")[-1]
            if "(" not in last:
                continue
            assert last[-1] == ')', "filter {f} sohuld end on closing parenthesis"
            last = last[:-1] # remove )
            # now remove (
            parenthesis_pos = last.find("(")
            last = last[parenthesis_pos+1:]
            # parse params
            params = {}
            for item in last.split(","):
                item = item.split("=")
                first = item[0]
                if len(item) > 1:
                    second = item[1]
                else:
                    second = True
                params[first] = second
            res.append(params)
        if len(res) == 0:
            res.append(None)
        return res

    @classmethod
    def construct(cls, context: ActionContext, parents):
        """Construct an instance of the current action, adhering to
        specification of parameters or choosen action variants as specified by
        filters."""
        most_specific = context.most_specific_filters(parents, cls.name())
        parameters = cls.parse_parameters(most_specific)
        return cls(context, parents, parameters[0])

    @classmethod
    def construct_all(cls, context: ActionContext, parents):
        """Construct all combinations of instances of the current action, that
        adhere to the specification of parameters or choosen action variants as
        specified by filters."""
        most_specific = context.most_specific_filters(parents, cls.name())
        parameters = cls.parse_parameters(most_specific)
        return [cls(context, parents, param) for param in parameters]

    def __str__(self):
        return self.__class__.__name__


class SequenceAction(Action):
    # List of Action classes for each step in the sequence
    steps = []

    def __init__(self, context, parents, actions: 'list[Action]'):
        super().__init__(context, parents)
        self.actions = actions

    def run(self, input):
        failed_actions = []
        for action in self.actions:
            input = action(input)
            # copy error status
            if action.get_stat('error_status') != 'none':
                failed_actions.append(action.name())
            # copy stats from sub-actions
            for key, val in action._stats.items():
                self.set_stat(f"{action.name()}.{key}", val)
        if len(failed_actions) > 0:
            failed_str = ",".join(failed_actions)
            self.set_stat("error_status", f"failed({failed_str})")
        return input

    def get_stat_keys(self) -> 'list[str]':
        res = super().get_stat_keys()
        for action in self.actions:
            keys = action.get_stat_keys()
            res += [action.name() + "." + key for key in keys]
        return res

    @classmethod
    def construct(cls, context: ActionContext, parents):
        """ TODO

        """
        actions = []
        for step in cls.steps:
            action = step.construct(context, parents + [cls.name()])
            actions.append(action)
        return cls(context, parents, actions)

    @classmethod
    def construct_all(cls, context: ActionContext, parents):
        """ TODO

        """
        actions = []
        for step in cls.steps:
            step_actions = step.construct_all(context, parents + [cls.name()])
            actions.append(step_actions)
        res = []
        for combination in itertools.product(*actions):
            res.append(cls(context, parents, combination))
        return res

    def __str__(self):
        steps_str = ",".join([a.__str__() for a in self.actions])
        res = self.__class__.__name__ + "[" + steps_str + "]"
        return res


class ChoiceAction(Action):

    # Dict with names (strings) as keys and actions (actionclasses) as values
    options = {}

    def __init__(self, context, parents, option: Action):
        super().__init__(context, parents)
        self.option = option

    def run(self, input):
        res = self.option(input)
        self._stats = self.option.stats
        self.set_stat('option', self.option.name())
        return res

    def get_stat_keys(self) -> 'list[str]':
        return super().get_stat_keys() + self.option.get_stat_keys() + [
            "option",
        ]

    @classmethod
    @abstractmethod
    def default_action(cls):
        """Returns key / name of default action"""
        raise NotImplementedError(cls)

    @staticmethod
    def _parse_choice(filter):
        split = filter.split(":")
        assert len(split) > 0
        last = split[-1]
        if "(" in last:
            last = last.split("(")[0]
        return last

    @classmethod
    def construct(cls, context: ActionContext, parents):
        """ TODO

        """
        choice_filters = context.most_specific_choice(parents, cls.name())
        if len(choice_filters) == 0:  # no choice specified -> use default
            choice = cls.default_action()
        else:  # use first choice from filters
            choice = cls._parse_choice(choice_filters[0])
        Chosen_Class = cls.options[choice]
        action = Chosen_Class.construct(context, parents + [cls.name()])
        return cls(context, parents, action)

    @classmethod
    def construct_all(cls, context: ActionContext, parents):
        """ TODO

        """
        choice_filters = context.most_specific_choice(parents, cls.name())

        choices = []
        if len(choice_filters) == 0 and context.use_defaults:
            # no choice specified, use default
            choices.append(cls.default_action())
        elif len(choice_filters) == 0 and not context.use_defaults:
            # no choice, generate all
            choices += list(cls.options.keys())
        else:
            # choice given, generate those
            for f in choice_filters:
                choices.append(cls._parse_choice(f))

        chosen_classes = [cls.options[c] for c in choices]
        all_actions = []
        for Class in chosen_classes:
            actions = Class.construct_all(context, parents + [cls.name()])
            all_actions += actions
        return [cls(context, parents, action) for action in all_actions]

    def __str__(self):
        res = self.__class__.__name__ + "(" + self.option.__str__() + ")"
        return res
