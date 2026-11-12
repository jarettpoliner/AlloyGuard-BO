"""Outcome holder used by replay only; never passed into a policy."""
class OutcomeOracle:
    __slots__=("__outcomes","__revealed")
    def __init__(self,outcomes):
        self.__outcomes=dict(outcomes)
        self.__revealed=set()
    def reveal(self,alloy_id):
        if alloy_id in self.__revealed:
            raise ValueError("Composition already revealed")
        outcome=self.__outcomes[alloy_id]
        self.__revealed.add(alloy_id)
        return outcome
