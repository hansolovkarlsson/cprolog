/*  The zebra puzzle, also known as Einstein's riddle.

    ?- zebra(Houses, WaterDrinker, ZebraOwner).

    Each house is  house(Colour, Nation, Pet, Drink, Smoke).
*/

zebra(Houses, WaterDrinker, ZebraOwner) :-
    Houses = [house(_, norwegian, _, _, _), _, house(_, _, _, milk, _), _, _],
    member(house(red, english, _, _, _), Houses),
    right_of(house(green, _, _, _, _), house(ivory, _, _, _, _), Houses),
    next_to(house(_, norwegian, _, _, _), house(blue, _, _, _, _), Houses),
    member(house(_, spanish, dog, _, _), Houses),
    member(house(green, _, _, coffee, _), Houses),
    member(house(_, ukrainian, _, tea, _), Houses),
    member(house(_, _, snails, _, old_gold), Houses),
    member(house(yellow, _, _, _, kools), Houses),
    next_to(house(_, _, _, _, chesterfield), house(_, _, fox, _, _), Houses),
    next_to(house(_, _, _, _, kools), house(_, _, horse, _, _), Houses),
    member(house(_, _, _, orange_juice, lucky_strike), Houses),
    member(house(_, japanese, _, _, parliament), Houses),
    member(house(_, WaterDrinker, _, water, _), Houses),
    member(house(_, ZebraOwner, zebra, _, _), Houses).

right_of(A, B, [B, A, _, _, _]).
right_of(A, B, [_, B, A, _, _]).
right_of(A, B, [_, _, B, A, _]).
right_of(A, B, [_, _, _, B, A]).

next_to(A, B, Houses) :- right_of(A, B, Houses).
next_to(A, B, Houses) :- right_of(B, A, Houses).
