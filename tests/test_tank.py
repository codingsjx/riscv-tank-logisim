import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from rv32 import Machine,build


class TankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.words,cls.labels=build(ROOT)

    def setUp(self):
        self.m=Machine(self.words)
        self.m.mem[0x708]=0
        self.m.until(lambda m:m.pc==self.labels['main'])

    def call(self,name,a0=0,a1=0):
        self.m.reg[10],self.m.reg[11]=a0,a1
        self.m.call(self.labels[name])
        return self.m.reg[10]

    def tile(self,pos):return self.m.mem[0x100+4*pos]
    def sprite(self,pos):return (self.m.mem[0x800+4*(pos//8)]>>((pos%8)*4))&15
    def active_bullets(self):return [p for p in range(0x80,0xc0,16) if self.m.mem.get(p+8,0)]
    def poll(self,keys):
        self.m.set_keys(keys);self.m.set_keys(0)
        self.m.pc=self.labels['main'];self.m.step()
        self.m.until(lambda m:m.pc==self.labels['main'])
    def bullet(self,pos,direction,owner=0,slot=0x80):
        for offset,value in [(0,pos),(4,direction),(8,1),(12,owner)]:self.m.mem[slot+offset]=value

    def test_initial_world(self):
        self.assertEqual((self.m.mem[0],self.m.mem[8],self.m.mem[20],self.m.mem[28]),(0,3,2,1))
        self.assertEqual((self.sprite(0xd7),self.sprite(0x37),self.sprite(0xe7)),(4,10,3))
        self.assertEqual(self.tile(0x97),1)
        self.assertEqual(self.tile(0x63),2)

    def test_world_border(self):
        for p in range(256):
            if p//16 in (0,15) or p%16 in (0,15):self.assertEqual(self.tile(p),2)

    def test_turn_and_move(self):
        self.assertEqual(self.call('move_actor',64,1),1)
        self.assertEqual((self.m.mem[64],self.m.mem[68]),(0xd8,1))

    def test_blocked_turn_by_brick_steel_and_base(self):
        for pos,direction,target in [(0xa7,0,0x97),(0x73,0,0x63),(0xd7,2,0xe7)]:
            self.m.mem[64]=pos
            self.assertEqual(self.call('move_actor',64,direction),0)
            self.assertEqual((self.m.mem[64],self.m.mem[68]),(pos,direction))
            self.assertNotEqual(self.tile(target),0)

    def test_tanks_do_not_overlap(self):
        self.m.mem[64]=0x38
        self.assertEqual(self.call('move_actor',64,3),0)
        self.assertEqual(self.m.mem[64],0x38)

    def test_no_wrapping_at_world_edges(self):
        for pos,direction in [(0x00,0),(0x1f,1),(0xf4,2),(0x40,3)]:
            self.assertEqual(self.call('next_cell',pos,direction),0xffffffff)

    def test_player_projectile_limit(self):
        self.assertEqual([self.call('fire_actor',64) for _ in range(3)],[1,1,0])
        self.assertEqual(len(self.active_bullets()),2)
        self.assertEqual(self.m.mem[40],2)

    def test_enemy_projectile_limit(self):
        self.assertEqual(self.call('fire_actor',80),1)
        self.assertEqual(self.call('fire_actor',80),0)
        self.assertEqual(self.call('fire_actor',96),1)

    def test_projectile_moves_one_cell_per_tick(self):
        self.call('fire_actor',64)
        self.call('update_bullets')
        self.assertEqual(self.m.mem[0x80],0xc7)
        self.assertEqual(self.m.mem[0x88],1)

    def test_player_destroys_brick_and_scores(self):
        self.bullet(0xa7,0)
        self.call('update_bullets')
        self.assertEqual((self.tile(0x97),self.m.mem[4],self.m.mem[32],self.m.mem[0x88]),(0,10,10,0))

    def test_enemy_can_destroy_brick_without_player_points(self):
        self.bullet(0x87,2,1)
        self.call('update_bullets')
        self.assertEqual((self.tile(0x97),self.m.mem[4],self.m.mem[0x88]),(0,0,0))

    def test_steel_absorbs_projectile(self):
        self.bullet(0x73,0)
        self.call('update_bullets')
        self.assertEqual((self.tile(0x63),self.m.mem[4],self.m.mem[0x88]),(2,0,0))

    def test_player_kills_enemy(self):
        self.m.mem[0]=1
        self.bullet(0x47,0)
        self.call('update_bullets')
        self.assertEqual((self.m.mem[88],self.m.mem[20],self.m.mem[4]),(0,1,100))

    def test_last_enemy_kill_wins(self):
        self.m.mem[0]=1;self.m.mem[104]=0;self.m.mem[20]=1
        self.bullet(0x47,0)
        self.call('update_bullets')
        self.assertEqual((self.m.mem[0],self.m.mem[24],self.m.mem[20]),(4,3,0))

    def test_enemy_hit_respawns_and_grants_shield(self):
        self.m.mem[0]=1
        self.bullet(0xc7,2,1)
        self.call('update_bullets')
        self.assertEqual((self.m.mem[8],self.m.mem[64],self.m.mem[36]),(2,0xd7,6))
        self.assertFalse(self.active_bullets())
        self.call('damage_player')
        self.assertEqual(self.m.mem[8],2)

    def test_losing_last_life_ends_game(self):
        self.m.mem[8]=1
        self.call('damage_player')
        self.assertEqual((self.m.mem[0],self.m.mem[24],self.m.mem[72]),(3,1,0))

    def test_either_side_can_destroy_base(self):
        for owner in (0,1):
            self.call('game_reset');self.m.mem[0]=1
            self.bullet(0xd7,2,owner)
            self.call('update_bullets')
            self.assertEqual((self.m.mem[0],self.m.mem[24],self.m.mem[28],self.tile(0xe7)),(3,2,0,15))

    def test_enemy_ai_moves_and_fires_every_four_ticks(self):
        self.m.mem[0]=1
        for _ in range(3):self.call('game_tick')
        self.assertEqual(self.m.mem[80],0x37)
        self.call('game_tick')
        self.assertEqual((self.m.mem[80],self.m.mem[96]),(0x47,0x3b))
        self.assertEqual(len(self.active_bullets()),2)

    def test_pause_blocks_movement_fire_and_ticks(self):
        self.poll(16);self.poll(32)
        before=(self.m.mem[64],self.m.mem[12])
        self.poll(1|128|256)
        self.assertEqual((self.m.mem[64],self.m.mem[12]),before)
        self.assertFalse(self.active_bullets())
        self.poll(32);self.assertEqual(self.m.mem[0],1)

    def test_restart_preserves_best_and_rebuilds_bricks(self):
        self.call('add_score',100)
        self.m.mem[0x100+0x97*4]=0
        self.poll(64)
        self.assertEqual((self.m.mem[0],self.m.mem[4],self.m.mem[32],self.tile(0x97)),(0,0,100,1))

    def test_render_packed_tiles_and_all_directions(self):
        for direction in range(4):
            self.m.mem[68]=direction
            self.call('render')
            self.assertEqual(self.sprite(0xd7),4+direction)
        self.bullet(0xc7,0)
        self.call('render')
        self.assertEqual(self.sprite(0xc7),12)
        self.assertEqual(self.m.mem[0x740],0)
        self.assertEqual(self.m.mem[0x748],3)

    def test_movement_render_does_not_reset_physics_timer(self):
        self.poll(16)
        before=self.m.mem[16]
        self.poll(2)
        self.assertEqual(self.m.mem[16],before)

    def test_short_fire_click_and_manual_tick(self):
        self.poll(16)
        self.poll(128)
        self.assertEqual(len(self.active_bullets()),1)
        self.assertEqual(self.m.mem[12],0)
        self.poll(256)
        self.assertEqual((self.m.mem[12],self.m.mem[0x80]),(1,0xc7))

    def test_incremental_frame_matches_complete_world(self):
        self.m.mem[0]=1
        for tick in range(40):
            if tick%4==0:self.call('fire_actor',64)
            if tick%7==0:self.call('move_actor',64,1 if tick%14==0 else 3)
            self.call('game_tick');self.call('render')
            expected=[self.tile(p) for p in range(256)]
            for p in range(0x80,0xc0,16):
                if self.m.mem.get(p+8,0):expected[self.m.mem[p]]=12 if self.m.mem[p+12]==0 else 13
            for p in (64,80,96):
                if self.m.mem[p+8]:expected[self.m.mem[p]]=self.m.mem[p+4]+(4 if p==64 else 8)
            if self.m.mem[8]==0:expected[self.m.mem[64]]=14
            self.assertEqual([self.sprite(p) for p in range(256)],expected)
            if self.m.mem[0]!=1:break

    def test_incremental_render_reduces_instruction_work(self):
        before=self.m.cycles;self.call('render');incremental=self.m.cycles-before
        self.m.mem[44]=1
        before=self.m.cycles;self.call('render');full=self.m.cycles-before
        self.assertLess(incremental,full//2)


if __name__=='__main__':unittest.main(verbosity=2)
