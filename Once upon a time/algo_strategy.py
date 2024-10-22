import gamelib
import random
import math
import warnings
from sys import maxsize
import json

#global enemyattack = []

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""




class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.enemyMP = []
        self.enemyMPallin = []
        self.turns = []
        self.enemyHP = []
        # Proud Attr
        self.last_spawning_loc = []
        self.enemy_HP_last = -1

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(
            game_state.turn_number))
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)
        self.enemyHP.append(game_state.enemy_health)
        self.starter_strategy(game_state)
        self.enemy_HP_last = game_state.enemy_health
        
        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout.
        We will place turrets and walls as part of our initial setup.
        For offense, we will use scouts every two turns to try and score quickly.
        """
        # First, place basic defenses
        


        if game_state.turn_number < 3 :
            game_state.attempt_spawn(DEMOLISHER, [[24,10]], 5)
            game_state.attempt_spawn(SUPPORT,[[19,11]],1)
            
        elif game_state.turn_number % 2 == 1:
            self.send_scouts(game_state)
        

        self.build_defences(game_state)
        # Lastly, if we have spare SP, let's build some supports
        # support_locations_f1 = [[11, 9], [16, 9], [13, 6], [15, 8], [17, 7]]
        # game_state.attempt_spawn(SUPPORT, support_locations_f1)
        # game_state.attempt_upgrade([[16, 9], [11, 9], [15, 8], [17, 7]])

        # support_locations_f2 = [[10, 8], [9, 7]]
        # game_state.attempt_spawn(SUPPORT, support_locations_f2)
        # game_state.attempt_upgrade(support_locations_f2)




    def layer1(self, game_state):

        turret_locations = [[3,12], [24,12],[4,12],[23,12], [10,12], [17,12]]
        upgrade = [[3,12], [24,12]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(upgrade)

        wall_locations = [[10,12],[9,12],[11,12], [16,12],[17,12],[18,12]]

        game_state.attempt_spawn(WALL, wall_locations)
        



    def build_defences(self, game_state):
        """

        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
 
        initial_tower_locations = [[3,12], [24,12],[4,12],[23,12], [10,12], [17,12]]
        initial_walls_locations = [[2, 13], [25, 13], [4, 12], [23, 12]]
        upgrade_locations = [ [4, 15],[23, 15], [4, 12], [23, 12]]


        self.layer1(game_state)
        game_state.attempt_upgrade(initial_tower_locations)
        self.restall_low_health(game_state)
        
        
        
        #only upgrade wall
        initial_wall_upgrade_locations = [[2, 13], [3, 13],[4,12],[5,11],[22,11],[23,12],[24,13],[4,13],[23,13],[12, 12], [15, 12]]
        #game_state.attempt_spawn(TURRET, initial_tower_upgrade_locations)
        game_state.attempt_upgrade(initial_wall_upgrade_locations)

        # initial_walls_locations2= [[6, 10], [7, 10], [8, 10], [9, 10], [10, 10], [11, 10], [12, 10],[12, 12], [15, 12], [14, 10], [15, 10], [16, 10], [17, 10], [18, 10], [20, 10], [15, 9], [13, 7],  [11, 8], [14, 8],[12, 4], [13, 3], [14, 2]]
        # game_state.attempt_spawn(WALL, initial_walls_locations2)
        game_state.attempt_spawn(SUPPORT, [[11, 9], [16, 9]])

        mid_tower_locations = [[6,11],[12,11],[15, 11], [21, 11],[3,12]]
        game_state.attempt_spawn(TURRET, mid_tower_locations)
        #mid_tower_upgrade_locations = [[7, 9], [8,8], [9,7], [10,6]]
        game_state.attempt_upgrade(mid_tower_locations)
        # support_locations_f1 = [[11, 9], [16, 9], [13, 6], [15, 8], [17, 7]]
        # game_state.attempt_spawn(SUPPORT, support_locations_f1)
        game_state.attempt_upgrade([[16, 9], [11, 9]])

        #gate_location = [[3,12],[24,12]]
        #game_state.attempt_spawn(WALL,gate_location = [[3,12],[24,12]])

        if game_state.turn_number > 10:
            game_state.attempt_spawn(WALL, [[6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12], [16, 12], [17, 12], [18, 12], [19, 12], [20, 12], [21, 12], [22, 12]])

        


        #game_state.attempt_upgrade(initial_walls_locations)

        mid_tower_locations = [[6,11],[12,11],[15, 11], [21, 11],[3,12]]
        game_state.attempt_spawn(TURRET, mid_tower_locations)
        #mid_tower_upgrade_locations = [[7, 9], [8,8], [9,7], [10,6]]
        game_state.attempt_upgrade(mid_tower_locations)


        support_locations = [[20,10],[7,10]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)

        game_state.attempt_upgrade(initial_tower_locations)

        
        late_tower_locations = [[3,12], [24,12],[2,12],[25,12],[1,12],[26,12],[25,11],[2,11],[7,11],[8,11],[9,11],[10,11],[11,11],[16,11],[17,11],[18,11],[19,11],[20,11]]
        game_state.attempt_spawn(TURRET, late_tower_locations)
        game_state.attempt_upgrade(late_tower_locations)
        if game_state.get_resource(SP)>8:
            game_state.attempt_upgrade([[0, 13], [2, 13], [26, 13], [27, 13]])
            late_wall_locations = [[6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12], [16, 12], [17, 12], [18, 12], [19, 12], [20, 12], [21, 12], [22, 12]]
            game_state.attempt_spawn(WALL, late_wall_locations)
            game_state.attempt_upgrade(late_wall_locations)
            game_state.attempt_upgrade(initial_walls_locations)


        #support_locations3 = [[13, 1], [14, 1]]
        #game_state.attempt_spawn(SUPPORT, support_locations3)

        #mid_wall_locations = [[20, 12], [12, 7], [18, 8], [20, 11], [18, 9]]
        #game_state.attempt_spawn(WALL, mid_wall_locations)

        
        #game_state.attempt_upgrade(support_locations)
        #game_state.attempt_upgrade(WALL, initial_walls_points)
        #late_tower_locations = [[6,9], [7,8], [8,7], [9,6],[10,5]]
        #game_state.attempt_spawn(TURRET, late_tower_locations)
        #game_state.attempt_upgrade(late_tower_locations)
        #game_state.attempt_upgrade(mid_wall_locations)
        

    def attempt_spawn_upgraded(self, unit, locations, game_state):
        """
        This function attempts to spawn a upgraded version of the tower, if no enough cost, won't even spawn a basic version.
        """
        for loc in locations:
            if game_state.get_resource(SP) >= 2*game_state.type_cost(unit)[SP]:
                game_state.attempt_spawn(unit, loc)
                game_state.attempt_upgrade(loc)

    def restall_low_health(self, game_state):
        low_health_threshold = 0.5
        for i in range(28):
            for j in range(28):
                loc = [i, j]
                if game_state.game_map.in_arena_bounds(loc):
                    for unit in game_state.game_map[i, j]:
                        if unit.health < unit.max_health * low_health_threshold:
                            game_state.attempt_remove(loc)
                            

    def open(self, game_state):
        if game_state.turn_number % 3 == 2 and  game_state.turn_number >8:
            if self.enemyHP[-5] == self.enemyHP[-1] and game_state.turn_number >20:
                game_state.attempt_remove([19, 10]) 
            else:
                game_state.attempt_remove([13,10])
        else:
            if game_state.turn_number % 3 == 1:
                game_state.attempt_spawn(WALL,[[13, 10], [19, 10]])

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
        
        
            build_location = [location[0], location[1]+1]
        #    game_state.attempt_spawn(WALL, build_location)
        #    game_state.attempt_upgrade( build_location)
        #it gerate each round
        if game_state.turn_number < 10 and self.scored_on_locations:
            game_state.attempt_spawn(INTERCEPTOR, [location[0], location[1]], 1)
    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(
            friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    # custom method
    def send_scouts(self, game_state):
        """
        Send out scouts at random locations to defend our base from enemy moving units.
        """

        scout_spawn_location_options =[[3,10],[4,9], [5,8], [6,7], [7,6], [8,5], [9,4], [10,3], [11,2], [12,1], [13,0], [14,0],[15,1], [16,2], [17,3], [18,4], [19,5], [20,6], [21,7],[22,8],[23,9],[24,10]]
        
        best_location = self.least_damage_spawn_location(
            game_state, scout_spawn_location_options)
        
        if not best_location:
            game_state.attempt_spawn(DEMOLISHER, [24, 10], 4)
            game_state.attempt_spawn(SCOUT, [13, 0], 6)
            return
        game_state.attempt_spawn(SCOUT, best_location, 1000)

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def damage_estimated_from_spawn_location(self, game_state, location):
        gamelib.debug_write("location: {}".format(location))
        damage = 0
        path = game_state.find_path_to_edge(location)
        if path and any(path):
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * \
                    gamelib.GameUnit(TURRET, game_state.config).damage_i
        return damage

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        if not location_options or not any(location_options):
            return location_options

        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path and any(path):
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * \
                        gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)

        if not damages or not any(damages):
            return None

        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations))


        
        

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()