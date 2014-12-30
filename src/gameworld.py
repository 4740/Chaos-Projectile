"""
.. module:: gameworld
    :platform: Unix, Windows
    :synopsis: Container of all entities in game.
"""

import os
import pygame
import level
import components
import chaosparticle
import ai
import collectible

import quadTree

class GameWorld(object):
    """ Container of all entities in game.

    :Attribute:
        - *screen* (pygame.Surface): reference to the game screen
        - *level* (level.Level): current level
        :Components:
            - *mask* (int list): contains a number equal the amount of components of the entity, index of the element is entities ID
            - *appearance* (dictionary ID : components.Apperance): animations and images
            - *collider* (dictionary ID : components.Collider): hitboxes
            - *velocity* (dictionary ID : float tuple): velocity for movable entities
            - *direction* (dictionary ID : tuple): aim and attacks direction (das aendern, in den Player rein!!!)
            - *characters* (dictionary ID : ): enemies and player (das besser aufplitten ??!!)
            - *attacks* (dictionary ID : components.Attack): attacks of the characters
            - *player* (int): ID of single player
            - *ai* (dictionary ID : ai): all AI for  enemies
    """

    def __init__(self, screen, event_manager):
        """
        :param screen: game screen
        :type screen: python.Surface
        :param event_managere: event manager
        :type event_manager: events.EventManager
        """
        self.level = level.Level()
        self.screen = screen
        self.event_manager = event_manager

        #Components and entities
        self.mask = list()
        self.appearance = {}
        self.collider = {}
        self.velocity = {}
        self.direction = {}
        self.players = {}
        self.attacks = {}
        self.player = None
        self.ai = {}
        self.tags = {}
        self.hp = {}
        self.collectibles = {}
        
        self.inactive_entities = list()
        self.to_remove = list()
        
        #Create all game entities
        
        #Create characters
        #layer = self.level.tmx_data.getTileLayerByName("players")
        '''LayerWeite und Breite auslesen!! Sowie die Nummer'''
        #Temp list
        fields = list()
        walls = list()
        #Get layer width and height in tiles
        layer_width = len(self.level.tmx_data.layers[0].data)
        layer_height = len(self.level.tmx_data.layers[0].data[0])
        for layer_index in range(len(self.level.tmx_data.layers)):
            for x in range(layer_width):
                for y in range(layer_height):
                    if self.level.tmx_data.layers[layer_index].name == "characters":
                        tile = self.level.tmx_data.get_tile_properties(x, y, layer_index)
                        if tile:
                            if "type" in tile:
                                if tile["type"] == "enemy":
                                    #Create enemies
                                    position = (x*64+32, y*64+32)
                                    self.create_enemy(position)
                                elif tile["type"] == "player":
                                    #Create player
                                    position = (x*64+32, y*64+32)
                                    self.create_player(position)
                    if self.level.tmx_data.layers[layer_index].name == "decoration front":
                        tile = self.level.tmx_data.get_tile_properties(x, y, layer_index)
                        if tile:
                            if "type" in tile:
                                if tile["type"] == "field":
                                    #Add fields
                                    mass = int(tile["mass"])
                                    position = (x*64+32, y*64+32)
                                    fields.append(chaosparticle.Field(position, mass))
                    if self.level.tmx_data.layers[layer_index].name == "characters":
                        tile = self.level.tmx_data.get_tile_properties(x, y, layer_index)
                        if tile:
                            if "type" in tile:
                                if tile["type"] == "heal_potion":
                                    #Add fields
                                    recovery = int(tile["recovery"])
                                    tags = list()
                                    tags.append("heal_potion")
                                    collider = components.Collider(x*64, y*64, 64, 64, tags)
                                    temp = pygame.image.load(os.path.join('data', 'heal_pot.png'))
                                    heal_sprite = components.Appearance(temp.convert_alpha())
                                    heal_sprite.rect.center = collider.center
                                    heal_pot = collectible.HealPotion(self, self.event_manager, recovery)
                                    colle_ID = self.create_entity((heal_sprite, heal_pot, collider))
                                    heal_pot.entity_ID = colle_ID
                                if tile["type"] == "skill_up":
                                    #Add fields
                                    collider = components.Collider(x*64, y*64, 64, 64)
                                    temp = pygame.image.load(os.path.join('data', 'skill_pot.png'))
                                    skillup_sprite = components.Appearance(temp.convert_alpha())
                                    skillup_sprite.rect.center = collider.center
                                    skillup_pot = collectible.SkillUp(self, self.event_manager)
                                    colle_ID = self.create_entity((skillup_sprite, skillup_pot, collider))
                                    skillup_pot.entity_ID = colle_ID
                                if tile["type"] == "portal":
                                    #Add fields
                                    x_pos = int(tile["x"])
                                    y_pos = int(tile["y"])
                                    x_pos, y_pos = x_pos*64+32, y_pos*64+32
                                    collider = components.Collider(x*64, y*64, 64, 64)
                                    temp = pygame.image.load(os.path.join('data', 'portal.png'))
                                    portal_sprite = components.Appearance(temp.convert_alpha())
                                    portal_sprite.rect.center = collider.center
                                    portal = collectible.Portal(self, self.event_manager, x_pos, y_pos)
                                    colle_ID = self.create_entity((portal_sprite, portal, collider))
                                    portal.entity_ID = colle_ID
                    #Create walls
                    if self.level.tmx_data.layers[layer_index].name == "walls":
                        tile = self.level.tmx_data.get_tile_image(x, y, layer_index)
                        tile_properties = self.level.tmx_data.get_tile_properties(x, y, layer_index)
                        if tile:
                            tags = list()
                            if tile_properties:
                                if "type" in tile_properties:
                                    if tile_properties["type"] == "corner":
                                        #Tile is a corner
                                        tags.append("corner")
                            coll = components.Collider(x*64, y*64, 64, 64, tags)
                            walls.append(coll)
        #Characters and their attacks are created, so fields can be added
        for field in fields:
            self.create_field(field.position, field.mass)
        #Create Level curse:
        #---
        damage = 10
        cooldown = 30
        position = [0,0]
        
        temp_eff = pygame.image.load(os.path.join('data', 'attack_effect.png'))
        eff_sprite = components.Appearance(temp_eff.convert_alpha(), 62, 62, [6], [cooldown])
        eff_sprite.play_animation_till_end = True
        eff_sprite.play_once = True
        effect_ID = self.create_entity((eff_sprite, ))
        curse_AI = ai.Level1_curse(self, 0, self.event_manager)
        curse_ID = self.create_entity((curse_AI, ))
        curse_AI.entity_ID = curse_ID 
        particle_emitter = components.Attack(self, damage, cooldown, position,
                                             1, 'proj.png', 60,
                                             [1, 0], [0, 0], 15, effect_ID)
        attack_list = list()
        attack_list.append(particle_emitter)
        self.add_component_to_entity(curse_ID, attack_list)
        #---
        #Quad Tree
        self.tree = quadTree.QuadTree(walls)

    def create_field(self, position, mass):
        """Adds field to all attacks.
        
        :param position: position of the field
        :type postion: 2d list
        :param mass: mass
        :type mass: int
        """
        for attacks in self.attacks.itervalues():
            for attack in attacks:
                attack.add_field(chaosparticle.Field(position, mass))

    def create_player(self, position):
        """Create player.
        
        :param position: position where player is created
        :type position: 2d list
        """
        #Create players hp gui
        temp = pygame.image.load(os.path.join('data', 'hp.png')).convert_alpha()
        hp = components.Health(150, 3, temp)
        c_hp = (hp, hp.current_image)
        hp_ID = self.create_entity(c_hp)
        #Players hitbox, it is 50 pixel width and 96 pixel height
        coll = components.Collider(position[0], position[1], 50, 96)
        vel = components.Velocity([0, 0])
        #Create players animations
        temp = pygame.image.load(os.path.join('data', 'char.png')).convert_alpha()
        anim_list = [4, 4, 3, 10]
        anim_time_list = [240, 180, 44, 60]
        anim = components.Appearance(temp, 128, 128, anim_list, anim_time_list)
        anim.rect.center = coll.center
        direction = components.Direction([1, 0])
        player = components.Player(0, hp_ID, )
        c = (direction, coll, vel, anim, player)
        self.player = self.create_entity(c)
        #Now create the players orb
        #It is created afterward, so orb will be
        #displayed over players sprite
        temp = pygame.image.load(os.path.join('data', 'orb.png'))
        orb_sprite = components.Appearance(temp.convert_alpha())
        c_orb = (orb_sprite,)
        orb_ID = self.create_entity(c_orb)
        #Set orb ID
        self.players[self.player].orb_ID = orb_ID
        #Create players attacks
        #Attack 1:
        damage = 10
        cooldown = 30
        position = coll.center
        
        temp_eff = pygame.image.load(os.path.join('data', 'attack_effect.png'))
        eff_sprite = components.Appearance(temp_eff.convert_alpha(), 62, 62, [6], [cooldown])
        eff_sprite.play_once = True
        eff_sprite.play_animation_till_end = True
        c_eff = (eff_sprite,)
        effect_ID = self.create_entity(c_eff)
        particle_emitter = components.Attack(self, damage, cooldown, position,
                                             1, 'proj.png', 60,
                                             self.direction[self.player], [0, 0], 15, effect_ID)
        attack_list = list()
        attack_list.append(particle_emitter)
        self.add_component_to_entity(self.player, attack_list)

    def create_enemy(self, position):
        """Create an enemy.
        
        :param position: position where enemy is created
        :type position: 2d list
        """
        #Enemy's hitbox, it is 50 pixel width and 96 pixel height
        coll = components.Collider(position[0], position[1], 50, 96)
        vel = components.Velocity([0, 0])
        #Create enemy's animations
        temp = pygame.image.load(os.path.join('data', 'char.png')).convert_alpha()
        anim_list = [4, 4, 3, 10]
        anim_time_list = [240, 60, 44, 60]
        anim = components.Appearance(temp, 128, 128, anim_list, anim_time_list)
        anim.rect.center = coll.center
        direction = components.Direction([1, 0])
        hp = components.Health(100)
        c = (coll, direction, vel, anim, hp)
        enemy_ID = self.create_entity(c)

        enemy_AI = ai.AI_1(self, enemy_ID, self.event_manager)
        self.add_component_to_entity(enemy_ID, enemy_AI)

        #Create enemies attacks
        #attack 1
        damage = 10
        position = coll.center
        particle_emitter = components.Attack(self, damage, 30, position,
                                             3, 'proj.png', 60,
                                             self.direction[enemy_ID], [0, 0], 15)
        attack_list = list()
        attack_list.append(particle_emitter)
        self.add_component_to_entity(enemy_ID, attack_list)

    def add_component_to_entity(self, entity_ID, component):
        if isinstance(component, components.Collider):
            self.collider[entity_ID] = component
        elif isinstance(component, components.Velocity):
            self.velocity[entity_ID] = component
        elif isinstance(component, components.Appearance):
            self.appearance[entity_ID] = component
        elif isinstance(component, components.Direction):
            self.direction[entity_ID] = component
        elif isinstance(component, components.Player):
            self.players[entity_ID] = component
        elif isinstance(component, list):
            if isinstance(component[0], components.Attack):
                self.attacks[entity_ID] = component
        elif isinstance(component, ai.AI):
            self.ai[entity_ID] = component
        elif isinstance(component, components.Health):
            self.hp[entity_ID] = component
        elif isinstance(component, collectible.Collectible):
            self.collectibles[entity_ID] = component
        #Increase amount of components of the entity
        self.mask[entity_ID] += 1

    def create_entity(self, c):
        """Adds an entity to the game world.
        
        :param c: all components of new entity
        :type c: components list
        :rtype: ID of the new entity
        """
        entity = self.get_empty_entity()
        for component in c:
            self.add_component_to_entity(entity, component)
        #Return ID of new entity
        return entity

    def get_empty_entity(self):
        """Gets not used index as an ID for new entity.
        
        :rtype: ID of an empty entity
        """
        for entity in range(len(self.mask)):
            #There is unused ID, if there are no components assigned
            if self.mask[entity] == 0:
                return entity
        #If mask isn't long enough, add new element
        entity = len(self.mask) 
        self.mask.append(0)
        return entity

    def active_entity(self, entity_ID):
        
        return not entity_ID in self.inactive_entities

    def destroy_entity(self, entity_ID):
        #Clear mask, this entity has no components more
        self.mask[entity_ID] = 0
        #Clear dictionaries
        if entity_ID in self.collider:
            del self.collider[entity_ID]
        if entity_ID in self.velocity:
            del self.velocity[entity_ID]
        if entity_ID in self.appearance:
            del self.appearance[entity_ID]
        if entity_ID in self.direction:
            del self.direction[entity_ID]
        if entity_ID in self.players:
            del self.players[entity_ID]
        if entity_ID in self.attacks:
            del self.attacks[entity_ID]
        if entity_ID in self.ai:
            #self.event_manager.unregister_listener(self.ai[entity_ID])
            del self.ai[entity_ID]
        if entity_ID in self.hp:
            del self.hp[entity_ID]
        if entity_ID in self.collectibles:
            del self.collectibles[entity_ID]
        