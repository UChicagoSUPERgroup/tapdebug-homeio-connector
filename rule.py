from typing import List, Dict, Any, Tuple

from device import Device

class Expression(object):
    def __init__(self, var: Device, comp: str, val):
        """

        :param var: the variable
        :param comp: comparator
        :param val: the value
        """
        self.var = var
        self.comp = comp
        self.val = val

    def _simpleCheck(self, var: Device, val):
        if var == self.var:
            self_val = type(val)(self.val)
            if self.comp == '=':
                return val == self_val
            elif self.comp == '!=':
                return val != self_val
            elif self.comp == '<':
                return val < self_val
            elif self.comp == '>':
                return val > self_val
            elif self.comp == '<=':
                return val <= self_val
            else:  # self.comp == '>=
                return val >= self_val
        else:
            return False
    
    def __eq__(self, o: object) -> bool:
        return self.var == o.var and self.comp == o.comp and self.val == o.val
    
    def __str__(self) -> str:
        return str(self.var.name) + self.comp + str(self.val)


class ActionExpression(Expression):
    def __init__(self, var: Device, comp: str, val):
        """

        :param var:
        :param comp: this time the comparator must be '='
        :param val:
        """
        super(ActionExpression, self).__init__(var, '=', val)
    
    def __eq__(self, o: object) -> bool:
        return super().__eq__(o)


class ConditionExpression(Expression):
    def __init__(self, var: Device, comp: str, val):
        """

        :param var:
        :param comp:
        :param val:
        """
        super(ConditionExpression, self).__init__(var, comp, val)

    def check(self, var: Device, val):
        return self._simpleCheck(var, val)

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o)


class TriggerExpression(Expression):
    def __init__(self, var: Device, comp: str, val, hold_t: int=None, delay: int=None):
        """

        :param var:
        :param comp: this time the comparator must be '='
        :param val:
        :param hold_t: time for "state has been true for more than xxx time" in seconds
        :param delay: time for "xxx time after event happens" in seconds
        """
        super(TriggerExpression, self).__init__(var, comp, val)
        if hold_t is not None and delay is not None:
            raise Exception("a trigger cannot be both types of timing expression")
        self.hold_t = hold_t
        self.delay = delay


    def check(self, event):
        if not isinstance(event, TriggerExpression):
            raise TypeError("event should be an Event Expression")
        # if self.hold_t is not None:
        #     return event.hold_t == self.hold_t and self._simpleCheck(event.var, event.val)
        # if self.delay is not None:
        #     return event.delay == self.delay and self._simpleCheck(event.var, event.val)
        return self._simpleCheck(event.var, event.val)

    def checkTrigger(self, val):
        if self.hold_t is not None or self.delay is not None:
            return False
        else:
            return self._simpleCheck(self.var, val)
    
    def __eq__(self, o: object) -> bool:
        return super().__eq__(o) and self.hold_t == o.hold_t and self.delay == o.delay

    def __str__(self):
        return 'hold: %s, delay: %s, %s%s%s' % (self.hold_t, self.delay, self.var, self.comp, self.val)


EventExpression = TriggerExpression


class TAPRule(object):
    # a regular rule, with a symbol for deletion
    def __init__(self, trigger: TriggerExpression, condition: List[ConditionExpression], action: ActionExpression, plain=False):
        self.plain = plain

        # trigger, condition and action
        self.trigger_e = trigger
        self.condition = condition
        self.action = action

    def trigger(self, event: EventExpression, pre_condition_dict: Dict[str, Any]):
        cond_sat = all([cond.check(cond.var, pre_condition_dict[cond.var]) for cond in self.condition])
        cond_sat = cond_sat and not self.trigger_e.checkTrigger(pre_condition_dict[self.trigger_e.var])

        return self.action, self.trigger_e.check(event) and cond_sat

    def is_clock(self):
        # check if the trigger is "if it becomes xx:xx" (clock trigger)
        return self.trigger_e.var.address == 65 and \
               self.trigger_e.var.datatype == 'DateTime' and \
               self.trigger_e.var.typ == 'Memory'

    def is_hold(self):
        return self.trigger_e.hold_t is not None

    def __eq__(self, o: object) -> bool:
        return self.trigger_e == o.trigger_e and self.condition == o.condition and self.action == o.action
    
    def __str__(self) -> str:
        trigger = str(self.trigger_e)
        condition = ' AND '.join([str(cond) for cond in self.condition])
        action = str(self.action)

        return 'IF %s WHILE %s, THEN %s' % (trigger, condition, action)

    def __repr__(self) -> str:
        return str(self)
