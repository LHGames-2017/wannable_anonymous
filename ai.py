from flask import Flask, request
from structs import *
import json
import numpy

app = Flask(__name__)

def create_action(action_type, target):
    actionContent = ActionContent(action_type, target.__dict__)
    return json.dumps(actionContent.__dict__)

def create_move_action(target):
    return create_action("MoveAction", target)

def create_attack_action(target):
    return create_action("AttackAction", target)

def create_collect_action(target):
    return create_action("CollectAction", target)

def create_steal_action(target):
    return create_action("StealAction", target)

def create_heal_action():
    return create_action("HealAction", "")

def create_purchase_action(item):
    return create_action("PurchaseAction", item)

def deserialize_map(serialized_map):
    """
    Fonction utilitaire pour comprendre la map
    """
    serialized_map = serialized_map[1:]
    rows = serialized_map.split('[')
    column = rows[0].split('{')
    deserialized_map = [[Tile() for x in range(20)] for y in range(20)]
    for i in range(len(rows) - 1):
        column = rows[i + 1].split('{')

        for j in range(len(column) - 1):
            infos = column[j + 1].split(',')
            end_index = infos[2].find('}')
            content = int(infos[0])
            x = int(infos[1])
            y = int(infos[2][:end_index])
            deserialized_map[i][j] = Tile(content, x, y)

    return deserialized_map

def bot():
    """
    Main de votre bot.
    """
    map_json = request.form["map"]

    # Player info

    encoded_map = map_json.encode()
    map_json = json.loads(encoded_map)
    p = map_json["Player"]
    pos = p["Position"]
    x = pos["X"]
    y = pos["Y"]
    house = p["HouseLocation"]
    player = Player(p["Health"], p["MaxHealth"], Point(x,y),
                    Point(house["X"], house["Y"]), p["Score"],
                    p["CarriedResources"], p["CarryingCapacity"])

    # Map
    serialized_map = map_json["CustomSerializedMap"]
    deserialized_map = deserialize_map(serialized_map)

    otherPlayers = []
    '''
    for player_dict in map_json["OtherPlayers"]:
        for player_name in player_dict.keys():
            player_info = player_dict[player_name]
            p_pos = player_info["Position"]
            player_info = PlayerInfo(player_info["Health"],
                                     player_info["MaxHealth"],
                                     Point(p_pos["X"], p_pos["Y"]))
            otherPlayers.append({player_name: player_info })
            '''
    # Printing the map
    for line in deserialized_map:
        out = ""
        for tile in line:
            if tile.Content == TileContent.Empty:
                out += ("E")
            elif tile.Content == TileContent.Wall:
                out += ("M")
            elif tile.Content == TileContent.House:
                out += ("H")
            elif tile.Content == TileContent.Lava:
                out += ("L")
            elif tile.Content == TileContent.Resource:
                out += ("R")
            elif tile.Content == TileContent.Shop:
                out += ("S")
            elif tile.Content == TileContent.Player:
                out += ("P")
        print(out)

    if player.CarriedRessources >= player.CarryingCapacity:
        # On revient a la maison
        return goTo(deserialized_map, player.Position, player.HouseLocation)
    else:
        # On cherche les ressources
        resList = []
        for i in range(len(deserialized_map)):
            for j in range(len(deserialized_map[i])):
                if deserialized_map[i][j].Content == TileContent.Resource:
                    resList.append(Point(j, i))
        # On trouve la plus proche
        print(resList)
        objectif = resList[0]
        for res in resList:
            if res.Distance(res, Point(10, 10)) < objectif.Distance(res, Point(10, 10)):
                objectif = res
        # On decide si on collecte ou on y va
        if estACote(Point(10, 10), objectif):
            create_collect_action(objectif)
        else:
            return goTo(deserialized_map, player.Position, objectif)

    # Simple decision making
    # On tue les ennemis faible
    for enemy in otherPlayers:
        if estACote(player.Position, ennemy.Position):
            return create_attack_action(ennemy)

    # return decision
    return create_move_action(player.Position - Point(1, 0))

def goTo(dmap, src, dest):
    if 10 > dest.Y and dmap[9][10].Content == TileContent.Empty:
        return create_move_action(src - Point(1, 0))
    elif 10 < dest.Y and dmap[11][10].Content == TileContent.Empty:
        return create_move_action(src + Point(1, 0))
    elif 10 > dest.X and dmap[10][9].Content == TileContent.Empty:
        return create_move_action(src - Point(0, 1))
    elif 10 < dest.X and dmap[10][11].Content == TileContent.Empty:
        return create_move_action(src + Point(0, 1))

def estACote(posPlayer, point):
    if (posPlayer.X - point.X == 1 or posPlayer.X - point.X == -1) and (posPlayer.Y - point.Y == 1 or posPlayer.Y - point.Y == -1):
        return True
    return False

def calculateDamage(attacker, defender):
    pass

@app.route("/", methods=["POST"])
def reponse():
    """
    Point d'entree appelle par le GameServer
    """
    return bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
