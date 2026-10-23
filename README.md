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
--

Everything nondeterministic is injectable. latency lets tests pass 0 so they run 
instantly. rng lets you pass a seeded random.Random(42) for reproducible readings. 
schedule controls failures. This is dependency injection without a framework.

next(self._schedule, False) means “use the script while it lasts, then succeed 
forever.” schedule=[True, True] reads naturally as “fail twice, then recover.”

The radio detail is real. foF2 is the highest frequency the F2 layer reflects 
straight up. Multiplying by an M(3000)F2 factor of about 3 gives a ballpark MUF for 
a 3000 km skip.

