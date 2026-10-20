# Working Notes

A few notes on design for this exercise:
*check_health()* raises instead of returning a status. 
Feeds only report what they observed. Deciding what to do about failures 
(retry, count attempts, mark DOWN) belongs in the monitor. That keeps each feed trivial 
and puts the fault-tolerance logic in one testable place.

*FeedUnavailable* subclasses ConnectionError. Callers can catch it specifically, and 
generic network-error handling still works.

*HealthResult* is frozen. Results are facts about a moment in time, so nothing should 
mutate them after creation.

*Protocol*, not a base class. Real feeds and test fakes never need to inherit anything. 
They only need the right shape. 
