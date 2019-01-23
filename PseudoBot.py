import logging
import hlt
from hlt import Direction, Position
from hlt import constants
from collections import defaultdict
from time import time
from statistics import median

game = hlt.Game()

me = game.me
game_map = game.game_map
max_turns = constants.MAX_TURNS


# Tuning parameters
threshold = constants.MAX_HALITE * 0.9
size = 4
rush = max_turns * .93
TILL = max_turns * .6
##

logging.info("RUSH: {}".format(rush))
game.ready("PseudoBotV6")

logging.info("Successfully created Bot! my player id is: {}".format(game.my_id))


def calculate_gain(ship):
    """
    While returning to the shipyard/dropoff location checks if the move will result in lowering
    the ship's current halite amount than the specified threshold.

    :param ship: takes into account the current halite stored in the ship.

    returns: halite amount the ship will be left with

    """
    loss_percentage = .1
    amount = game_map[ship.position].halite_amount
    ship_amount = ship.halite_amount
    gain = ship_amount - int(amount * loss_percentage)
    return gain


def unpack(position):
    """
    :param position: Takes a class object Position(x, y).

    returns: a tuple of the (x, y) co-ordinate.
    """
    return (position.x, position.y)


def oppose(direction):
    """
    takes direction as inputs and returns opposite of that direction. for e.g. direction: (1, 0)
    will result in (-1, 0).

    :param direction: direction as tuple of (x, y) co-ordinate.

    returns: direction in opposite to the provided direction.
    """

    return (direction[0] if direction[0] == 0
            else -1 * direction[0] if direction[0] != 0
            else direction[0],
            direction[1] if direction[1] == 0
            else -1 * direction[1] if direction[1] != 0
            else direction[1])


def get_directions(source, destination):
    """
    takes source (current position) of the ship and destination (the ship to move towards) for the
    next turn.

    :param source: ship's current position as Position object.
    :param destination: ship to move towards as Position object.

    returns: East if x co-ordinate of destination greater than(>) x co-ordinate of source and West if
    x co-ordinate of destination is less than(<) x co-ordinate of source.

    """
    return (Direction.East if destination.x > source.x
            else Direction.West if destination.x < source.x
            else None,
            Direction.South if destination.y > source.y
            else Direction.North if destination.y < source.y
            else None)


def rm_surrounding(pos, ship):
    """
    removes off positions surrounding the target and current ship's current position.

    :param pos: target position that should not be taken into consideration for the next ship.
    :param ship: ship position that should not be taken into consideration for the next ship.

    returns: returns list of target position, positions surrounding the target and ship's position
    """
    temp = [unpack(pos)] + [unpack(game_map.normalize(pos + Position(*direction))) for direction in Direction.get_all_cardinals()] + \
        [unpack(ship.position)]
    return temp


def get_order(this_ship, other_ship):
    """
    Returns the ship objects by following status: (Returning, Exploring) as we need to check whether the exploring
    ship's cargo does not go below 0 as that will result in the ship crashing with the returning ship.

    :param this_ship: current ship.
    :param other_ship: The ship that is currently in current ship's way.

    returns: returns ship according to their statuses i.e. Returning, Exploring.
    """
    this_ship_status = ship_status[this_ship.id][0]
    if this_ship_status == ret:
        return this_ship, other_ship
    return other_ship, this_ship


def map_scan():
    """
    Scans the whole map for their halite amounts(resources) and returns the median of those values.
    """
    halite_dict = {
        (x, y): game_map[Position(x, y)].halite_amount
        for y in range(0, game_map.height)
        for x in range(0, game_map.width)
    }

    return median(halite_dict.values())


def safe_scan(this_ship, size):
    """
    Scans the area to be covered defined by size with respect to the current ship and does not take
    into account the positions that are currently occupied and positions that are already assigned
    to previous ships as a dictionary with "(x, y)" cordinates and "halite amount" as key, value pairs.

    :param this_ship: current ship.
    :param size: covers 2 * size from current ship's position - size to current ship's position + size in both
    (x, y) directions.

    returns: tuple of co-ordinate of maximum halite available and halite dict.
    """

    halite_dict = {
        (x, y): game_map[Position(x, y)].halite_amount
        for y in range(this_ship.position.y - size, this_ship.position.y + size)
        for x in range(this_ship.position.x - size, this_ship.position.x + size)
        if not game_map[Position(x, y)].is_occupied and (x, y) not in owned_positions and (x, y) not in IGNORE
    }

    TARGET = max(halite_dict, key=halite_dict.get)
    MEDIAN = median(halite_dict.values())

    ignore = rm_surrounding(Position(*TARGET), this_ship)

    return TARGET, ignore, MEDIAN


def Navigator(ship, target, index, rushHour=False):
    """
    Navigates the ship to the appropriate direction so as to reduce the distance between target.


    :param ship: the ship to move.
    :param target: the destination.
    :param index: the index at which the the move will be assigned for that ship.
    :param rushHour: False by default. when True available ships will rush toward closest
    shipyard or dropoff location.

    returns: Possible direction in (1, 0), (0, 1), (-1, 0), (0, -1) else (0, 0)
    """
    source = game_map.normalize(ship.position)
    destination = game_map.normalize(target)

    distance = abs(destination - source)
    direction_x, direction_y = get_directions(source, destination)

    moves = []
    if distance.x != 0:
        moves.append(direction_x if distance.x < (game_map.width / 2)
                     else Direction.invert(direction_x))
    if distance.y != 0:
        moves.append(direction_y if distance.y < (game_map.height / 2)
                     else Direction.invert(direction_y))

    for move in moves:
        target_pos = ship.position.directional_offset(move)
        if not rushHour:
            if game_map[target_pos].is_occupied and not force:
                try:
                    other_ship = me.get_ship([id for id in ship_status.keys() if unpack(ship_status[id][1]) == unpack(target_pos)][0])

                    if ship_status[ship.id][0] != ship_status[other_ship.id][0]:
                        logging.info("currentShip: {} OtherShip: {}".format(ship_status[ship.id][0], ship_status[other_ship.id][0]))
                        move = unpack(other_ship.position - ship.position)

                        if other_ship.id not in commanded_ships:
                            returning, exploring = get_order(ship, other_ship)

                            if calculate_gain(exploring) > 0 or unpack(exploring.position) == unpack(me.shipyard.position):
                                game_map[other_ship.position.directional_offset(oppose(move))].mark_unsafe(other_ship)
                                ship_status[other_ship.id][1] = other_ship.position.directional_offset(oppose(move))
                                commands.append(other_ship.move(oppose(move)))
                                commanded_ships[other_ship.id] = index
                                game_map[ship.position.directional_offset(move)].mark_unsafe(ship)
                                return move
                            else:
                                continue
                        else:
                            logging.info("OtherShipID: {} is in commanded ships\n{}".format(other_ship.id, commands))
                            logging.info("Wanted to swap with: {}".format(ship.id))
                            # pass

                    elif ship_status[ship.id][0] == ship_status[other_ship.id][0]:

                        logging.info("ShipID: {} and OtherShipID: {} is behind other".format(ship.id, other_ship.id))

                except Exception as e:
                    logging.info("ship will be availabe for commanding on next turn.")
                    logging.info("ERROR: {}".format(e))

            elif force:
                return move

            else:
                game_map[target_pos].mark_unsafe(ship)
                return move

        # rushHour logic. DO NOT CHANGE!
        else:
            if not game_map[target_pos].is_occupied:
                game_map[target_pos].mark_unsafe(ship)
                return move
            elif target_pos == me.shipyard.position:
                return move

    valid = []
    for move in [oppose(move) for move in moves]:
        target_pos = ship.position.directional_offset(move)
        if not game_map[target_pos].is_occupied and game_map[target_pos].halite_amount != 0:
            valid.append((move, game_map[target_pos].halite_amount))
        else:
            continue

    if valid:
        pseudoMove = max(valid, key=lambda x: x[1])[0]
        game_map[ship.position.directional_offset(pseudoMove)].mark_unsafe(ship)
        return pseudoMove

    return Direction.Still


ship_status = defaultdict(list)
target_positions = defaultdict(tuple)
explore = "Exploring"
ret = "Returning"

while True:
    start = time()
    game.update_frame()

    # temporary storage per turn
    ATTACK_mode = False
    commands = []
    IGNORE = []
    owned_positions = []
    commanded_ships = defaultdict(int)
    force = False

    other_players = {player_id: game.players[player_id].get_ships() for player_id in game.players if player_id is not game.my_id}

    for player_id in other_players:
        for ship in other_players[player_id]:
            if unpack(ship.position) == unpack(me.shipyard.position):
                force = True

    for index, ship in enumerate(me.get_ships()):

        if ship.halite_amount < threshold:
            ship_status[ship.id] = [explore,
                                    ship.position]

        elif ship.halite_amount >= threshold:
            ship_status[ship.id] = [ret,
                                    ship.position]

        TARGET, ignore, MEDIAN = safe_scan(ship, size)
        IGNORE += ignore
        target_positions[ship.id] = TARGET

        owned_positions.append(TARGET)

        if index % 10 == 0:
            MEDIAN = map_scan()

        if game.turn_number < rush:

            if ship_status[ship.id][0] == explore and ship.id not in commanded_ships:
                max_halite_cord = target_positions[ship.id]

                if game_map[ship.position].halite_amount > MEDIAN * .7:
                    move = Direction.Still
                    commands.append(ship.move(move))
                    commanded_ships[ship.id] = index

                else:
                    move = Navigator(ship, Position(*max_halite_cord), index)
                    ship_status[ship.id][1] = ship.position.directional_offset(move)
                    commands.append(ship.move(move))
                    commanded_ships[ship.id] = index

            if ship_status[ship.id][0] == ret and ship.id not in commanded_ships:

                if ship.position == me.shipyard.position:
                    ship_status[ship.id][0] = explore

                else:
                    gain = calculate_gain(ship)

                    if gain > threshold or ship.is_full:
                        move = Navigator(ship, me.shipyard.position, index)
                        commands.append(ship.move(move))
                        commanded_ships[ship.id] = index
                        ship_status[ship.id][1] = ship.position.directional_offset(move)

        else:
            move = Navigator(ship, me.shipyard.position, index, True)
            ship_status[ship.id][1] = ship.position.directional_offset(move)
            commands.append(ship.move(move))

    if game.turn_number < TILL and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        commands.append(me.shipyard.spawn())

    end = time()

    # logging.info("TARGETS: {}".format(target_positions))
    # logging.info([(ship.id, ship.position) for ship in me.get_ships()])
    # logging.info(ship_status)
    # logging.info("commands: {}".format(commands))
    logging.info('Time taken for completion of full turn: {}'.format(end - start))

    game.end_turn(commands)
