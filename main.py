import pygame
import sys
from enum import Enum 
import os 

LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60
TITULO = "Plataform Shooter"

PRETO = (0, 0, 0) 
BRANCO = (255, 255, 255)
VERDE = (0, 255, 0)      
VERMELHO = (255, 0, 0)    
AMARELO = (255, 255, 0) 

VELOCIDADE_JOGADOR = 5.0 
FORCA_PULO = -15.0 
GRAVIDADE = 0.8
PLAYER_LARGURA = 40 
PLAYER_ALTURA = 45  

PLAYER_ANIMATION_SPEED_MS = 90 
PLAYER_DEATH_ANIMATION_SPEED_MS = 150 

PROJ_LARGURA = 10
PROJ_ALTURA = 5
PROJ_VELOCIDADE = 10

ZUMBI_LARGURA = 35 
ZUMBI_ALTURA = 45  
ZUMBI_VIDA_INICIAL = 4
ZUMBI_VELOCIDADE = 1.0
ZOMBIE_ANIMATION_SPEED_MS = 150 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PLAYER_DYING = 3 
    GAME_OVER = 4    
    VICTORY = 5      
    QUIT = 6         

class TextRenderer:
    def __init__(self, font_name=None):
        self.font_name = font_name
        self.fonts = {}
    def _get_font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_name, size)
        return self.fonts[size]
    def draw(self, surface, texto, size, cor, x, y, center=True):
        fonte = self._get_font(size)
        superficie_texto = fonte.render(texto, True, cor)
        rect_texto = superficie_texto.get_rect()
        if center:
            rect_texto.center = (x, y)
        else:
            rect_texto.topleft = (x, y)
        surface.blit(superficie_texto, rect_texto)

class Projectile:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(0, 0, PROJ_LARGURA, PROJ_ALTURA)
        self.rect.center = (x, y)
        self.vel_x = PROJ_VELOCIDADE * direction
    def update(self):
        self.rect.x += self.vel_x
    def draw(self, surface):
        pygame.draw.rect(surface, AMARELO, self.rect)

class Zombie:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ZUMBI_LARGURA, ZUMBI_ALTURA)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.vel_y = 0.0
        self.health = ZUMBI_VIDA_INICIAL
        self.alive = True
        self.direction = -1 
        self.is_moving = False 
        
        self.idle_frame_right = None
        self.idle_frame_left = None
        self.walk_frames_right = []
        self.walk_frames_left = []
        self.current_frame_index = 0
        self.last_animation_update = pygame.time.get_ticks()
        self.walk_frame_count = 0 
        
        self._load_sprites() 

    def _load_sprites(self):
        fallback_surface = pygame.Surface((ZUMBI_LARGURA, ZUMBI_ALTURA))
        fallback_surface.fill(VERMELHO) 
        try:
            path_idle = resource_path('zombie_idle.png') 
            idle_original = pygame.image.load(path_idle).convert_alpha()
            self.idle_frame_right = pygame.transform.scale(
                idle_original, (ZUMBI_LARGURA, ZUMBI_ALTURA)
            )
            self.idle_frame_left = pygame.transform.flip(
                self.idle_frame_right, True, False
            )
        except Exception as e:
            self.idle_frame_right = fallback_surface
            self.idle_frame_left = pygame.transform.flip(fallback_surface, True, False)
        i = 1
        while True:
            try:
                filename = f"zombie_walk{i}.png" 
                path_walk = resource_path(filename)
                walk_original = pygame.image.load(path_walk).convert_alpha()
                walk_scaled = pygame.transform.scale(
                    walk_original, (ZUMBI_LARGURA, ZUMBI_ALTURA)
                )
                self.walk_frames_right.append(walk_scaled)
                self.walk_frames_left.append(
                    pygame.transform.flip(walk_scaled, True, False)
                )
                i += 1
            except FileNotFoundError:
                break 

        self.walk_frame_count = len(self.walk_frames_right)
        if self.walk_frame_count == 0:
            self.walk_frames_right = [self.idle_frame_right]
            self.walk_frames_left = [self.idle_frame_left]
            self.walk_frame_count = 1

    def take_damage(self, amount):
        if not self.alive: return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def _move_horizontal(self, player_rect, all_zombies): 
        if not self.alive: return
        
        dist_x = player_rect.centerx - self.rect.centerx
        move_x = 0.0
        
        intended_to_move = abs(dist_x) > ZUMBI_VELOCIDADE 
        
        if not intended_to_move:
            self.is_moving = False 
            return 
        
        if dist_x < 0: 
            move_x = -ZUMBI_VELOCIDADE
            self.direction = -1 
        else: 
            move_x = ZUMBI_VELOCIDADE
            self.direction = 1  

        initial_pos_x = self.pos_x

        self.pos_x += move_x
        self.rect.x = round(self.pos_x) 
        
        for z in all_zombies:
            if z is self or not z.alive: continue
            
            if self.rect.colliderect(z.rect):
                if move_x > 0: 
                    self.rect.right = z.rect.left
                elif move_x < 0: 
                    self.rect.left = z.rect.right
                
                self.pos_x = float(self.rect.x) 
                break 
        
        epsilon = 0.1 
        actually_moved = abs(self.pos_x - initial_pos_x) > epsilon
        self.is_moving = actually_moved
                
    def _apply_physics(self, plataformas):
        if not self.alive: return
        self.vel_y += GRAVIDADE
        self.pos_y += self.vel_y
        self.rect.y = round(self.pos_y)
        for plat in plataformas:
            if self.rect.colliderect(plat.rect): 
                if self.vel_y > 0: 
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = plat.rect.bottom
                    self.vel_y = 0 
                self.pos_y = float(self.rect.y)

    def _update_animation(self):
        if not self.alive or not self.is_moving: 
            return 
        now = pygame.time.get_ticks()
        time_elapsed = now - self.last_animation_update
        if time_elapsed > ZOMBIE_ANIMATION_SPEED_MS:
            self.last_animation_update = now
            self.current_frame_index = (self.current_frame_index + 1) % self.walk_frame_count
            
    def update(self, player_rect, plataformas, all_zombies): 
        if not self.alive: return
        self._move_horizontal(player_rect, all_zombies) 
        self._apply_physics(plataformas)
        self._update_animation() 
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)

    def draw(self, surface):
        if not self.alive: 
            return 
        image_to_draw = None
        if self.direction == 1: 
            if self.is_moving:
                image_to_draw = self.walk_frames_right[self.current_frame_index]
            else:
                image_to_draw = self.idle_frame_right
        else: 
            if self.is_moving:
                image_to_draw = self.walk_frames_left[self.current_frame_index]
            else:
                image_to_draw = self.idle_frame_left
        surface.blit(image_to_draw, self.rect)

class Platform:
    def __init__(self, x, y, width, height, tile_image_name):
        self.rect = pygame.Rect(x, y, width, height)
        self.tile_image = None
        self.tile_width = 0
        self.tile_height = 0 
        try:
            path_tile = resource_path(tile_image_name)
            original_tile = pygame.image.load(path_tile).convert_alpha()
            tile_height = self.rect.height
            self.tile_height = tile_height 
            orig_w, orig_h = original_tile.get_size()
            tile_width = int(orig_w * (tile_height / orig_h))
            self.tile_image = pygame.transform.scale(original_tile, (tile_width, tile_height))
            self.tile_width = tile_width
        except Exception as e:
            pass

    def draw(self, surface):
        if self.tile_image is None or self.tile_width == 0:
            pygame.draw.rect(surface, (0, 255, 0), self.rect) 
            return
        current_x = self.rect.x
        while current_x < self.rect.right:
            remaining_width = self.rect.right - current_x
            if remaining_width < self.tile_width:
                clip_rect = pygame.Rect(0, 0, remaining_width, self.tile_height)
                surface.blit(self.tile_image, (current_x, self.rect.y), clip_rect)
            else:
                surface.blit(self.tile_image, (current_x, self.rect.y))
            current_x += self.tile_width

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_LARGURA, PLAYER_ALTURA)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.vel_y = 0.0 
        self.esta_no_chao = False
        self.direction = 1 
        
        self.state = "ALIVE" 
        self.death_animation_finished = False 

        self.is_moving = False 
        self.current_frame_index = 0
        self.last_animation_update = pygame.time.get_ticks() 
        
        self.run_frame_count = 0 
        self.run_frames_right = []
        self.run_frames_left = []
        self.idle_frame_right = None
        self.idle_frame_left = None
        self.death_frames = [] 
        self.death_frame_count = 0 

        self._load_sprites()
            
    def _load_sprites(self):
        fallback_surface = pygame.Surface((PLAYER_LARGURA, PLAYER_ALTURA))
        fallback_surface.fill((0, 0, 255)) 
        try:
            path_idle = resource_path('john_stopped.png') 
            idle_original = pygame.image.load(path_idle).convert_alpha()
            self.idle_frame_right = pygame.transform.scale(
                idle_original, (PLAYER_LARGURA, PLAYER_ALTURA)
            )
            self.idle_frame_left = pygame.transform.flip(
                self.idle_frame_right, True, False
            )
        except Exception as e:
            self.idle_frame_right = fallback_surface
            self.idle_frame_left = fallback_surface

        i = 1

        while True:
            try:
                filename = f"john_run{i}.png" 
                path_run = resource_path(filename)
                run_original = pygame.image.load(path_run).convert_alpha()
                run_scaled = pygame.transform.scale(
                    run_original, (PLAYER_LARGURA, PLAYER_ALTURA)
                )
                self.run_frames_right.append(run_scaled)
                self.run_frames_left.append(
                    pygame.transform.flip(run_scaled, True, False)
                )
                i += 1
            except FileNotFoundError:
                break 
            except Exception as e:
                break 

        self.run_frame_count = len(self.run_frames_right)
        if self.run_frame_count == 0:
            self.run_frames_right = [self.idle_frame_right]
            self.run_frames_left = [self.idle_frame_left]
            self.run_frame_count = 1
        i = 1
        while True:
            try:
                filename = f"john_defeated{i}.png" 
                path_death = resource_path(filename)
                death_original = pygame.image.load(path_death).convert_alpha()
                death_scaled = pygame.transform.scale(
                    death_original, (PLAYER_LARGURA, PLAYER_ALTURA) 
                )
                self.death_frames.append(death_scaled)
                i += 1
            except FileNotFoundError:
                break 
            except Exception as e:
                break 

        self.death_frame_count = len(self.death_frames)
        if self.death_frame_count == 0:
            self.death_frames = [self.idle_frame_right] 
            self.death_frame_count = 1

    def handle_input(self, event):
        if self.state != "ALIVE": 
            return None 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.jump()
            if event.key == pygame.K_SPACE:
                return self.shoot()
        return None 
    
    def shoot(self):
        return Projectile(self.rect.centerx, self.rect.centery, self.direction)
    
    def jump(self):
        if self.esta_no_chao:
            self.vel_y = FORCA_PULO
            self.esta_no_chao = False 
            
    def _move_horizontal(self):
        keys = pygame.key.get_pressed()
        self.is_moving = False 
        if keys[pygame.K_a]: 
            self.pos_x -= VELOCIDADE_JOGADOR
            self.direction = -1 
            self.is_moving = True 
        elif keys[pygame.K_d]: 
            self.pos_x += VELOCIDADE_JOGADOR
            self.direction = 1 
            self.is_moving = True
            
    def _apply_physics(self, plataformas):
        self.vel_y += GRAVIDADE
        self.pos_y += self.vel_y
        self.rect.y = round(self.pos_y)
        self.esta_no_chao = False 
        for plat in plataformas:
            if self.rect.colliderect(plat.rect): 
                if self.vel_y > 0: 
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0 
                    self.esta_no_chao = True
                elif self.vel_y < 0: 
                    self.rect.top = plat.rect.bottom
                    self.vel_y = 0 
                self.pos_y = float(self.rect.y)

    def _enforce_screen_boundaries(self):
        if self.pos_x < 0:
            self.pos_x = 0
        if self.pos_x + PLAYER_LARGURA > LARGURA_TELA:
            self.pos_x = LARGURA_TELA - PLAYER_LARGURA

    def _update_run_idle_animation(self):
        if not self.is_moving:
            self.current_frame_index = 0 
            return 
        now = pygame.time.get_ticks()
        time_elapsed = now - self.last_animation_update
        if time_elapsed > PLAYER_ANIMATION_SPEED_MS:
            self.last_animation_update = now
            self.current_frame_index = (self.current_frame_index + 1) % self.run_frame_count
            
    def _update_death_animation(self):
        if self.death_animation_finished: 
            return 
        now = pygame.time.get_ticks()
        time_elapsed = now - self.last_animation_update
        if time_elapsed > PLAYER_DEATH_ANIMATION_SPEED_MS:
            self.last_animation_update = now 
            self.current_frame_index += 1
            if self.current_frame_index >= self.death_frame_count:
                self.current_frame_index = self.death_frame_count - 1 
                self.death_animation_finished = True 
                
    def die(self):
        if self.state == "ALIVE": 
            self.state = "DYING"
            self.current_frame_index = 0 
            self.last_animation_update = pygame.time.get_ticks() 
            self.death_animation_finished = False
            self.vel_y = FORCA_PULO * 0.5 

    def update(self, plataformas):
        if self.state == "ALIVE":
            self._move_horizontal()
            self._apply_physics(plataformas)
            self._enforce_screen_boundaries()
            self._update_run_idle_animation() 
        elif self.state == "DYING":
            self._apply_physics(plataformas) 
            self._update_death_animation()
        
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)

    def draw(self, surface):
        image_to_draw = None
        if self.state == "ALIVE":
            if self.direction == 1: 
                if self.is_moving: image_to_draw = self.run_frames_right[self.current_frame_index]
                else: image_to_draw = self.idle_frame_right
            else: 
                if self.is_moving: image_to_draw = self.run_frames_left[self.current_frame_index]
                else: image_to_draw = self.idle_frame_left
        elif self.state == "DYING":
            frame_index = min(self.current_frame_index, self.death_frame_count - 1)
            image_to_draw = self.death_frames[frame_index]

        if image_to_draw:
            surface.blit(image_to_draw, self.rect)

class Game:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption(TITULO)
        self.relogio = pygame.time.Clock()
        
        self.estado_do_jogo = GameState.MENU
        self.text_renderer = TextRenderer() 
        
        self.player = None
        self.plataformas = [] 
        self.zombies = []
        self.projectiles = []
        
        self.platform_tile_name = "platform_tile.png" 
        self.background_tile_name = "platform_background.png" 
        
        self.background_image = None
        path_bg = resource_path(self.background_tile_name)
        self.background_image = pygame.image.load(path_bg).convert()

    def _draw_background(self):
        if self.background_image:
            w, h = self.background_image.get_size()
            if w == 0 or h == 0:
                self.tela.fill(PRETO)
                return
            for y in range(0, ALTURA_TELA, h):
                for x in range(0, LARGURA_TELA, w):
                    self.tela.blit(self.background_image, (x, y))
        else:
            self.tela.fill(PRETO)

    def _run_menu(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.estado_do_jogo = GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.estado_do_jogo = GameState.PLAYING
                    self._start_game() 

        self._draw_background() 
        
        self.text_renderer.draw(self.tela, "Plataforma Shooter", 70, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 4)
        self.text_renderer.draw(self.tela, "Controles:", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2 - 40)
        self.text_renderer.draw(self.tela, "A / D - Mover Esquerda / Direita", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.text_renderer.draw(self.tela, "W - Pular", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2 + 30)
        self.text_renderer.draw(self.tela, "ESPAÇO - Atirar", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2 + 60) 
        self.text_renderer.draw(self.tela, "ESC - Voltar ao Menu (no jogo)", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2 + 90)
        self.text_renderer.draw(self.tela, "Pressione ENTER para começar", 40, BRANCO, LARGURA_TELA // 2, ALTURA_TELA - 100)
        
        pygame.display.flip()
        self.relogio.tick(15) 
        
    def _start_game(self):
        self.player = Player(LARGURA_TELA // 2 - PLAYER_LARGURA // 2, 
                             ALTURA_TELA // 2 - PLAYER_ALTURA // 2) 
                             
        self.plataformas.clear()
        self.zombies.clear()
        self.projectiles.clear()
        
        plat_chao = Platform(x=0, y=ALTURA_TELA - 50, 
                             width=LARGURA_TELA, height=40, 
                             tile_image_name=self.platform_tile_name)
        plat_mid_long = Platform(x=200, y=ALTURA_TELA - 170, 
                            width=400, height=30, 
                            tile_image_name=self.platform_tile_name)
        plat_left_high = Platform(x=50, y=ALTURA_TELA - 300, 
                             width=110, height=30, 
                             tile_image_name=self.platform_tile_name)
        plat_right_high = Platform(x=630, y=ALTURA_TELA - 250, 
                              width=140, height=30, 
                              tile_image_name=self.platform_tile_name)
                              
        plat_top_center = Platform(x=600, y=ALTURA_TELA - 450, 
                                  width=200, height=30,        
                                  tile_image_name=self.platform_tile_name)

        self.plataformas = [
            plat_chao, plat_mid_long, plat_left_high, 
            plat_right_high, plat_top_center 
        ]

        z1 = Zombie(x=700, y=plat_chao.rect.top - ZUMBI_ALTURA)
        z2 = Zombie(x=300, y=plat_mid_long.rect.top - ZUMBI_ALTURA)
        z3 = Zombie(x=100, y=plat_left_high.rect.top - ZUMBI_ALTURA)
        z4_x = plat_right_high.rect.centerx - (ZUMBI_LARGURA // 2)
        z4_y = plat_right_high.rect.top - ZUMBI_ALTURA
        z4 = Zombie(x=int(z4_x), y=int(z4_y)) 
        
        z5_x = plat_top_center.rect.left + 30 
        z5_y = plat_top_center.rect.top - ZUMBI_ALTURA
        z5 = Zombie(x=int(z5_x), y=int(z5_y))
        
        z6_x = plat_top_center.rect.right - ZUMBI_LARGURA - 30 
        z6_y = plat_top_center.rect.top - ZUMBI_ALTURA
        z6 = Zombie(x=int(z6_x), y=int(z6_y)) 

        self.zombies = [z1, z2, z3, z4, z5, z6] 
        
    def _handle_game_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.estado_do_jogo = GameState.QUIT
                return 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    self.estado_do_jogo = GameState.MENU
                    return 
            if self.player and self.player.state == "ALIVE":
                new_projectile = self.player.handle_input(event)
                if new_projectile:
                    self.projectiles.append(new_projectile)
                
    def _handle_collisions(self):
        for p in self.projectiles[:]:
            if p.rect.right < 0 or p.rect.left > LARGURA_TELA:
                self.projectiles.remove(p)
                continue 
            for z in self.zombies:
                if z.alive and p.rect.colliderect(z.rect):
                    z.take_damage(1) 
                    self.projectiles.remove(p) 
                    break 
        if self.player and self.player.state == "ALIVE":
            for z in self.zombies:
                if z.alive and self.player.rect.colliderect(z.rect):
                    self.player.die() 
                    self.estado_do_jogo = GameState.PLAYER_DYING 
                    break 
                    
    def _check_for_victory(self):
        zumbis_vivos = [z for z in self.zombies if z.alive]
        if not zumbis_vivos: 
            self.estado_do_jogo = GameState.VICTORY
            
    def _update_entities(self):
        if self.player:
            self.player.update(self.plataformas)
        if self.estado_do_jogo == GameState.PLAYING:
            for p in self.projectiles:
                p.update()
        if self.estado_do_jogo == GameState.PLAYING:
            for z in self.zombies:
                z.update(self.player.rect, self.plataformas, self.zombies)
            
    def _draw_entities(self):
        for plat in self.plataformas:
            plat.draw(self.tela) 
        for z in self.zombies:
            z.draw(self.tela) 
        for p in self.projectiles:
            p.draw(self.tela)
        if self.player: 
            self.player.draw(self.tela)
        
    def _run_game(self):
        self._handle_game_events()
        self._update_entities()
        self._handle_collisions() 
        if self.estado_do_jogo == GameState.PLAYING:
            self._check_for_victory() 
        self._draw_background() 
        self._draw_entities()   
        pygame.display.flip()
        self.relogio.tick(FPS)

    def _run_player_dying(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.estado_do_jogo = GameState.QUIT
                return
        if self.player:
             self.player.update(self.plataformas) 
        self._draw_background()
        self._draw_entities() 
        pygame.display.flip()
        self.relogio.tick(FPS)
        if self.player and self.player.death_animation_finished:
            self.estado_do_jogo = GameState.GAME_OVER 

    def _run_game_over_screen(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.estado_do_jogo = GameState.QUIT
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: 
                    self.estado_do_jogo = GameState.MENU 
                    return
        self._draw_background() 
        self.text_renderer.draw(self.tela, "GAME OVER", 90, VERMELHO, LARGURA_TELA // 2, ALTURA_TELA // 3)
        self.text_renderer.draw(self.tela, "Você foi derrotado!", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.text_renderer.draw(self.tela, "Pressione ENTER para voltar ao Menu", 25, BRANCO, LARGURA_TELA // 2, ALTURA_TELA * 3 // 4)
        pygame.display.flip()
        self.relogio.tick(15) 

    def _run_victory_screen(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.estado_do_jogo = GameState.QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: 
                    self.estado_do_jogo = GameState.MENU
        self._draw_background() 
        self.text_renderer.draw(self.tela, "VITÓRIA!", 90, VERDE, LARGURA_TELA // 2, ALTURA_TELA // 3)
        self.text_renderer.draw(self.tela, "Você derrotou todos os zumbis!", 30, BRANCO, LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.text_renderer.draw(self.tela, "Pressione ENTER para voltar ao Menu", 25, BRANCO, LARGURA_TELA // 2, ALTURA_TELA * 3 // 4)
        pygame.display.flip()
        self.relogio.tick(15)
        
    def run(self):
        while self.estado_do_jogo != GameState.QUIT:
            if self.estado_do_jogo == GameState.MENU:
                self._run_menu()
            elif self.estado_do_jogo == GameState.PLAYING:
                self._run_game()
            elif self.estado_do_jogo == GameState.PLAYER_DYING: 
                self._run_player_dying()
            elif self.estado_do_jogo == GameState.GAME_OVER:    
                self._run_game_over_screen()
            elif self.estado_do_jogo == GameState.VICTORY:
                self. _run_victory_screen()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()