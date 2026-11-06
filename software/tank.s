# Tank Battle on the user's unmodified forwarding RISC-V CPU.
# State: 0 status,4 score,8 lives,12 tick,16 last cycle,20 enemies alive,
# 24 result (1 player lost/2 base lost/3 victory),28 base HP,32 best,
# 36 respawn shield,40 accepted player shots,44 full-redraw flag.
# 48 level (0..2),52 total enemies,56 reserve enemies,60 AI elapsed ticks.
# Extra RAM s7=0x900: upgrade, pickup position (-1 none), inventory,
# enemy HP1/HP2/HP3, bullet state, loot state, detour directions,
# and enemy max HP1/HP2/HP3. Kill/use counters are kept at later offsets.
# Tanks at 0x40/0x50/0x60; bullets at 0x80..0xbf. Record: pos,dir,active,owner.
# Previous entity cells 0xc0..0xdb; next projectile positions 0xe0..0xef;
# projectile cancellation flags 0xf0..0xff; terrain 0x100..0x4ff;
# nibble LUT 0x500..0x6ff; stack top 0xfc0.
# Keys 0x700, cycles 0x704, period 0x708 (0 manual), ACK 0x70c, requested level 0x710; bullet period 0x714 (0=2,1..3).
# HUD 0x740..0x760 (FRAME last); packed tile framebuffer 0x800..0x87f.
# Direction 0 up/1 right/2 down/3 left. Tank owner 0 player/1,2 enemy.
# s9/s10 are the main-loop dirty flag/events; s11 is MMIO base.
# Subroutines preserve every saved register they use.

start:
    addi sp, zero, 1008
    slli sp, sp, 2
    addi s11, zero, 1792
    addi s7, zero, 1152
    slli s7, s7, 1
    sw zero, 32(zero)
    addi t0, zero, 1280
    addi t3, zero, 1
    addi t4, zero, 8
lut_column:
    addi t1, zero, 16
    addi t2, zero, 0
lut_code:
    sw t2, 0(t0)
    add t2, t2, t3
    addi t0, t0, 4
    addi t1, t1, -1
    bne t1, zero, lut_code
    slli t3, t3, 4
    addi t4, t4, -1
    bne t4, zero, lut_column
    jal ra, game_reset
main:
    lw s10, 0(s11)
    sw s10, 12(s11)
    andi t0, s10, 64
    bne t0, zero, restart
    andi t0, s10, 16
    beq t0, zero, check_pause
    lw t0, 0(zero)
    beq t0, zero, begin_game
check_pause:
    andi t0, s10, 32
    beq t0, zero, controls
    lw t0, 0(zero)
    addi t1, zero, 1
    beq t0, t1, pause_game
    addi t1, zero, 2
    beq t0, t1, begin_game
controls:
    lw t0, 0(zero)
    addi t1, zero, 1
    bne t0, t1, main
    addi s9, zero, 0
    addi s8, zero, 0
    andi t0, s10, 1
    bne t0, zero, control_up
    andi t0, s10, 2
    bne t0, zero, control_right
    andi t0, s10, 4
    bne t0, zero, control_down
    andi t0, s10, 8
    beq t0, zero, control_fire
    addi a1, zero, 3
    jal zero, control_move
control_up:
    addi a1, zero, 0
    jal zero, control_move
control_right:
    addi a1, zero, 1
    jal zero, control_move
control_down:
    addi a1, zero, 2
control_move:
    addi a0, zero, 64
    jal ra, move_actor
    addi s9, zero, 1
control_fire:
    jal ra, collect_upgrade
    or s9, s9, a0
    andi t0, s10, 512
    beq t0, zero, check_fire
    jal ra, use_upgrade
    or s9, s9, a0
check_fire:
    andi t0, s10, 128
    beq t0, zero, check_time
    addi a0, zero, 64
    jal ra, fire_actor
    or s9, s9, a0
check_time:
    andi t0, s10, 256
    bne t0, zero, tick_now
    lw t0, 8(s11)
    beq t0, zero, check_dirty
    lw t1, 4(s11)
    lw t2, 16(zero)
    sub t1, t1, t2
    sltu t1, t1, t0
    bne t1, zero, check_dirty
tick_now:
    jal ra, game_tick
    addi s9, zero, 1
    addi s8, zero, 1
check_dirty:
    beq s9, zero, main
publish:
    jal ra, render
    beq s8, zero, main
    lw t0, 4(s11)
    sw t0, 16(zero)
    jal zero, main
restart:
    jal ra, game_reset
    jal zero, main
begin_game:
    addi t0, zero, 1
    sw t0, 0(zero)
    addi s8, zero, 1
    jal zero, publish
pause_game:
    addi t0, zero, 2
    sw t0, 0(zero)
    addi s8, zero, 1
    jal zero, publish

game_reset:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    lw s0, 32(zero)
    addi t0, zero, 0
    addi t1, zero, 64
reset_state:
    sw zero, 0(t0)
    addi t0, t0, 4
    bne t0, t1, reset_state
    sw s0, 32(zero)
    addi t0, s7, 0
    addi t1, s7, 88
reset_extra:
    sw zero, 0(t0)
    addi t0, t0, 4
    bne t0, t1, reset_extra
    addi t0, zero, -1
    sw t0, 4(s7)
    addi t0, zero, 3
    sw t0, 8(zero)
    lw t0, 16(s11)
    andi t0, t0, 3
    addi t1, zero, 3
    bne t0, t1, reset_level_valid
    addi t0, zero, 2
reset_level_valid:
    sw t0, 48(zero)
    addi t1, zero, 1
    sw t1, 12(s7)
    sw t1, 44(s7)
    addi t1, zero, 3
    sw t1, 16(s7)
    sw t1, 48(s7)
    slli t1, t0, 1
    sw t1, 56(zero)
    addi t1, t1, 2
    sw t1, 52(zero)
    sw t1, 20(zero)
    addi t0, zero, 1
    sw t0, 28(zero)
    sw t0, 44(zero)
    sw t0, 72(zero)
    sw t0, 88(zero)
    sw t0, 104(zero)
    sw t0, 92(zero)
    addi t0, zero, 2
    sw t0, 108(zero)
    sw t0, 84(zero)
    sw t0, 100(zero)
    sw zero, 68(zero)
    sw zero, 76(zero)
    addi t0, zero, 229
    sw t0, 64(zero)
    addi t0, zero, 55
    sw t0, 80(zero)
    addi t0, zero, 60
    sw t0, 96(zero)
    # Clear the extra actor slot before optional activation on higher levels.
    sw zero, 120(zero)
    # Advanced and hard levels keep a third enemy on the field.
    lw t1, 48(zero)
    beq t1, zero, no_third_enemy
    addi t0, zero, 75
    sw t0, 112(zero)
    addi t0, zero, 2
    sw t0, 116(zero)
    addi t0, zero, 1
    sw t0, 120(zero)
    sw t0, 124(zero)
no_third_enemy:
    # First wave starts with an elite and a normal.
    addi t1, zero, 3
    sw t1, 12(s7)
    sw t1, 44(s7)
    addi t1, zero, 1
    sw t1, 16(s7)
    sw t1, 48(s7)
    addi t1, zero, 3
    sw t1, 20(s7)
    sw t1, 52(s7)
    addi t0, zero, 128
    addi t1, zero, 192
reset_bullets:
    sw zero, 8(t0)
    addi t0, t0, 16
    bne t0, t1, reset_bullets
    addi t0, zero, 256
    addi t1, zero, 1280
clear_terrain:
    sw zero, 0(t0)
    addi t0, t0, 4
    bne t0, t1, clear_terrain
    addi t0, zero, 0
    addi t1, zero, 16
    addi t2, zero, 2
border_loop:
    slli t3, t0, 2
    addi t3, t3, 256
    sw t2, 0(t3)
    sw t2, 960(t3)
    slli t3, t0, 6
    addi t3, t3, 256
    sw t2, 0(t3)
    sw t2, 60(t3)
    addi t0, t0, 1
    bne t0, t1, border_loop
    # Steel cover: row 6, columns 3..5 and 10..12; row 11, 2,3,12,13.
    sw t2, 652(zero)
    sw t2, 656(zero)
    sw t2, 660(zero)
    sw t2, 680(zero)
    sw t2, 684(zero)
    sw t2, 688(zero)
    sw t2, 968(zero)
    sw t2, 972(zero)
    sw t2, 1008(zero)
    sw t2, 1012(zero)
    # Destructible bricks: row 9 columns 5..9, row 12 columns 4,5,9,10.
    addi t2, zero, 1
    addi t0, zero, 852
    addi t1, zero, 872
brick_loop:
    sw t2, 0(t0)
    addi t0, t0, 4
    bne t0, t1, brick_loop
    sw t2, 1040(zero)
    sw t2, 1044(zero)
    sw t2, 1060(zero)
    sw t2, 1064(zero)
    # Two-hit fortifications use tile 14; after one hit become ordinary brick.
    # Player starts at (5,14), beside the base. Keep its front entrance open.
    addi t2, zero, 14
    sw t2, 1112(zero)
    sw t2, 1120(zero)
    sw t2, 1176(zero)
    sw t2, 1184(zero)
    addi t2, zero, 1
    # Protect the base roof with a two-hit guard brick.
    addi t2, zero, 14
    sw t2, 1116(zero)
    addi t2, zero, 1

    lw t0, 48(zero)
    beq t0, zero, map_complete
    # Advanced: staggered brick cover across the central flanks.
    sw t2, 776(zero)
    sw t2, 784(zero)
    sw t2, 808(zero)
    sw t2, 816(zero)
    addi t1, zero, 1
    beq t0, t1, map_complete
    # Hard: more firing lanes and steel cover, never on spawn cells.
    sw t2, 592(zero)
    sw t2, 616(zero)
    sw t2, 904(zero)
    sw t2, 944(zero)
    addi t2, zero, 2
    sw t2, 724(zero)
    sw t2, 744(zero)
map_complete:
    addi t2, zero, 3
    sw t2, 1180(zero)
    lw t0, 0(s11)
    sw t0, 12(s11)
    jal ra, render
    lw t0, 4(s11)
    sw t0, 16(zero)
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)

# a0=current position, a1=direction -> a0=next position or -1.
next_cell:
    andi t0, a0, 15
    srli t1, a0, 4
    beq a1, zero, next_up
    addi t2, zero, 1
    beq a1, t2, next_right
    addi t2, zero, 2
    beq a1, t2, next_down
    beq t0, zero, next_invalid
    addi a0, a0, -1
    jalr zero, 0(ra)
next_up:
    beq t1, zero, next_invalid
    addi a0, a0, -16
    jalr zero, 0(ra)
next_right:
    addi t2, zero, 15
    beq t0, t2, next_invalid
    addi a0, a0, 1
    jalr zero, 0(ra)
next_down:
    addi t2, zero, 15
    beq t1, t2, next_invalid
    addi a0, a0, 16
    jalr zero, 0(ra)
next_invalid:
    addi a0, zero, -1
    jalr zero, 0(ra)

# a0=tank record, a1=direction. Turning is allowed even if movement is blocked.
move_actor:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    sw s1, 4(sp)
    addi s0, a0, 0
    sw a1, 4(s0)
    lw a0, 0(s0)
    jal ra, next_cell
    addi t0, zero, -1
    beq a0, t0, move_blocked
    addi s1, a0, 0
    slli t0, a0, 2
    addi t0, t0, 256
    lw t0, 0(t0)
    bne t0, zero, move_blocked
    addi t0, zero, 64
    addi t1, zero, 128
check_actor_overlap:
    beq t0, s0, overlap_next
    lw t2, 8(t0)
    beq t2, zero, overlap_next
    lw t2, 0(t0)
    beq t2, s1, move_blocked
overlap_next:
    addi t0, t0, 16
    bne t0, t1, check_actor_overlap
    sw s1, 0(s0)
    addi a0, zero, 1
    jal zero, move_return
move_blocked:
    addi a0, zero, 0
move_return:
    lw s1, 4(sp)
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)

# a0=tank record -> a0=1 if a projectile was accepted, otherwise zero.
fire_actor:
    addi t0, zero, 128
    addi t1, zero, 0
    addi t2, zero, 0
    lw t3, 12(a0)
    addi t6, zero, 192
fire_scan:
    lw t4, 8(t0)
    beq t4, zero, fire_empty
    lw t4, 12(t0)
    bne t4, t3, fire_scan_next
    addi t2, t2, 1
    jal zero, fire_scan_next
fire_empty:
    bne t1, zero, fire_scan_next
    addi t1, t0, 0
fire_scan_next:
    addi t0, t0, 16
    bne t0, t6, fire_scan
    beq t1, zero, fire_rejected
    beq t3, zero, player_fire_limit
    bne t2, zero, fire_rejected
    jal zero, fire_accept
player_fire_limit:
    lw t4, 0(s7)
    sltu t4, zero, t4
    addi t4, t4, 2
    sltu t4, t2, t4
    beq t4, zero, fire_rejected
fire_accept:
    lw t0, 0(a0)
    sw t0, 0(t1)
    lw t0, 4(a0)
    sw t0, 4(t1)
    addi t0, zero, 1
    sw t0, 8(t1)
    sw t3, 12(t1)
    bne t3, zero, fire_success
    lw t0, 40(zero)
    addi t0, t0, 1
    sw t0, 40(zero)
fire_success:
    addi a0, zero, 1
    jalr zero, 0(ra)
fire_rejected:
    addi a0, zero, 0
    jalr zero, 0(ra)

# a0=points, maintain session best score.
add_score:
    lw t0, 4(zero)
    add t0, t0, a0
    sw t0, 4(zero)
    lw t1, 32(zero)
    sltu t2, t1, t0
    beq t2, zero, score_done
    sw t0, 32(zero)
score_done:
    jalr zero, 0(ra)

damage_player:
    lw t0, 36(zero)
    bne t0, zero, damage_done
    lw t0, 8(zero)
    addi t0, t0, -1
    sw t0, 8(zero)
    beq t0, zero, player_dead
    addi t0, zero, 229
    addi t1, zero, 80
    addi t2, zero, 128
respawn_check:
    lw t3, 8(t1)
    beq t3, zero, respawn_next
    lw t3, 0(t1)
    bne t3, t0, respawn_next
    addi t0, t0, 4
    addi t1, zero, 80
    jal zero, respawn_check
respawn_next:
    addi t1, t1, 16
    bne t1, t2, respawn_check
    sw t0, 64(zero)
    sw zero, 68(zero)
    addi t0, zero, 6
    sw t0, 36(zero)
    jal zero, clear_danger
player_dead:
    sw zero, 72(zero)
    addi t0, zero, 3
    sw t0, 0(zero)
    addi t0, zero, 1
    sw t0, 24(zero)
clear_danger:
    addi t0, zero, 128
    addi t1, zero, 192
clear_danger_loop:
    sw zero, 8(t0)
    addi t0, t0, 16
    bne t0, t1, clear_danger_loop
damage_done:
    jalr zero, 0(ra)

# Predict all four endpoints before moving anything. Only player/enemy pairs
# cancel. Mark every colliding pair before applying flags, so slot order cannot
# decide a multi-projectile collision. Walls retain their normal precedence.
resolve_bullet_collisions:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    sw s2, 16(sp)
    sw s3, 12(sp)
    addi s0, zero, 128
    addi s1, zero, 224
predict_bullet:
    sw zero, 16(s1)
    lw t0, 8(s0)
    beq t0, zero, predict_invalid
    lw a0, 0(s0)
    lw a1, 4(s0)
    jal ra, next_cell
    addi t0, zero, -1
    beq a0, t0, predict_store
    slli t0, a0, 2
    addi t0, t0, 256
    lw t0, 0(t0)
    beq t0, zero, predict_store
predict_invalid:
    addi a0, zero, -1
predict_store:
    sw a0, 0(s1)
    addi s0, s0, 16
    addi s1, s1, 4
    addi t0, zero, 192
    bne s0, t0, predict_bullet
    addi s0, zero, 128
    addi s1, zero, 224
projectile_pair_outer:
    lw t0, 0(s1)
    addi t1, zero, -1
    beq t0, t1, projectile_outer_next
    addi s2, s0, 16
    addi s3, s1, 4
projectile_pair_inner:
    lw t0, 0(s3)
    addi t1, zero, -1
    beq t0, t1, projectile_inner_next
    lw t0, 12(s0)
    lw t1, 12(s2)
    sltu t0, zero, t0
    sltu t1, zero, t1
    beq t0, t1, projectile_inner_next
    lw t0, 0(s1)
    lw t1, 0(s3)
    beq t0, t1, projectile_pair_hit
    lw t2, 0(s2)
    bne t0, t2, projectile_inner_next
    lw t2, 0(s0)
    bne t1, t2, projectile_inner_next
projectile_pair_hit:
    addi t0, zero, 1
    sw t0, 16(s1)
    sw t0, 16(s3)
projectile_inner_next:
    addi s2, s2, 16
    addi s3, s3, 4
    addi t0, zero, 192
    bne s2, t0, projectile_pair_inner
projectile_outer_next:
    addi s0, s0, 16
    addi s1, s1, 4
    addi t0, zero, 176
    bne s0, t0, projectile_pair_outer
    addi s0, zero, 128
    addi s1, zero, 240
apply_projectile_cancel:
    lw t0, 0(s1)
    beq t0, zero, apply_cancel_next
    sw zero, 8(s0)
apply_cancel_next:
    addi s0, s0, 16
    addi s1, s1, 4
    addi t0, zero, 192
    bne s0, t0, apply_projectile_cancel
    lw s3, 12(sp)
    lw s2, 16(sp)
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    jalr zero, 0(ra)

update_bullets:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    sw s2, 16(sp)
    sw s3, 12(sp)
    jal ra, resolve_bullet_collisions
    addi s0, zero, 128
bullet_loop:
    lw t0, 8(s0)
    beq t0, zero, bullet_next
    lw a0, 0(s0)
    lw a1, 4(s0)
    jal ra, next_cell
    addi t0, zero, -1
    beq a0, t0, bullet_expire
    addi s2, a0, 0
    lw s1, 12(s0)
    slli t0, s2, 2
    addi t0, t0, 256
    lw t1, 0(t0)
    addi t2, zero, 1
    beq t1, t2, bullet_brick
    addi t2, zero, 14
    beq t1, t2, bullet_guard
    addi t2, zero, 2
    beq t1, t2, bullet_expire
    addi t2, zero, 3
    beq t1, t2, bullet_base
    bne s1, zero, bullet_player
    addi s3, zero, 80
bullet_enemy_scan:
    lw t0, 8(s3)
    beq t0, zero, bullet_enemy_next
    lw t0, 0(s3)
    beq t0, s2, bullet_kill_enemy
bullet_enemy_next:
    addi s3, s3, 16
    addi t0, zero, 128
    bne s3, t0, bullet_enemy_scan
    jal zero, bullet_advance
bullet_player:
    lw t0, 72(zero)
    beq t0, zero, bullet_advance
    lw t0, 64(zero)
    bne t0, s2, bullet_advance
    jal ra, damage_player
    jal zero, bullet_expire
bullet_kill_enemy:
    srli t3, s3, 2
    add t3, t3, s7
    lw t0, -8(t3)
    lw t1, 0(s7)
    slti t1, t1, 2
    addi t2, zero, 2
    sub t2, t2, t1
    sub t0, t0, t2
    slt t1, zero, t0
    beq t1, zero, enemy_destroyed
    sw t0, -8(t3)
    jal zero, bullet_expire
enemy_destroyed:
    sw zero, -8(t3)
    sw zero, 8(s3)
    lw t0, 60(s7)
    addi t0, t0, 1
    sw t0, 60(s7)
    lw t0, 24(t3)
    addi t1, zero, 3
    bne t0, t1, enemy_drop_done
    lw t0, 32(s7)
    addi t0, t0, 1
    sw t0, 32(s7)
    lw t0, 4(s7)
    addi t1, zero, -1
    bne t0, t1, enemy_drop_done
    sw s2, 4(s7)
enemy_drop_done:
    lw t0, 20(zero)
    addi t0, t0, -1
    sw t0, 20(zero)
    addi a0, zero, 100
    jal ra, add_score
    sw zero, 8(s0)
    lw t0, 20(zero)
    bne t0, zero, bullet_next
    addi t0, zero, 4
    sw t0, 0(zero)
    addi t0, zero, 3
    sw t0, 24(zero)
    jal zero, bullets_done
bullet_guard:
    addi t1, zero, 1
    sw t1, 0(t0)
    addi a0, s2, 0
    addi a1, zero, 1
    jal ra, draw_tile
    jal zero, bullet_expire
bullet_brick:
    sw zero, 0(t0)
    addi a0, s2, 0
    addi a1, zero, 0
    jal ra, draw_tile
    bne s1, zero, bullet_expire
    addi a0, zero, 10
    jal ra, add_score
    jal zero, bullet_expire
bullet_base:
    addi t1, zero, 15
    sw t1, 0(t0)
    addi a0, s2, 0
    addi a1, zero, 15
    jal ra, draw_tile
    sw zero, 28(zero)
    sw zero, 8(s0)
    addi t0, zero, 3
    sw t0, 0(zero)
    addi t0, zero, 2
    sw t0, 24(zero)
    jal zero, bullets_done
bullet_advance:
    sw s2, 0(s0)
    jal zero, bullet_next
bullet_expire:
    sw zero, 8(s0)
bullet_next:
    addi s0, s0, 16
    addi t0, zero, 192
    bne s0, t0, bullet_loop
bullets_done:
    lw s3, 12(sp)
    lw s2, 16(sp)
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    jalr zero, 0(ra)

collect_upgrade:
    addi a0, zero, 0
    lw t0, 4(s7)
    lw t1, 64(zero)
    bne t0, t1, collect_done
    lw t0, 8(s7)
    slti t1, t0, 3
    beq t1, zero, collect_done
    addi t0, t0, 1
    sw t0, 8(s7)
    lw t0, 32(s7)
    addi t0, t0, -1
    sw t0, 32(s7)
    bne t0, zero, collect_success
    addi t0, zero, -1
    sw t0, 4(s7)
collect_success:
    addi a0, zero, 1
collect_done:
    jalr zero, 0(ra)

use_upgrade:
    addi a0, zero, 0
    lw t0, 8(s7)
    beq t0, zero, use_done
    lw t1, 0(s7)
    slti t2, t1, 2
    beq t2, zero, use_repair
    addi t1, t1, 1
    sw t1, 0(s7)
    jal zero, use_consume
use_repair:
    lw t1, 8(zero)
    slti t2, t1, 3
    beq t2, zero, use_done
    addi t1, t1, 1
    sw t1, 8(zero)
use_consume:
    addi t0, t0, -1
    sw t0, 8(s7)
    lw t0, 24(s7)
    addi t0, t0, 1
    sw t0, 24(s7)
    addi a0, zero, 1
use_done:
    jalr zero, 0(ra)

# Simple chase AI: update once per four physics ticks, then try to fire.
enemy_ai:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    sw s1, 4(sp)
    sw s2, 0(sp)
    addi s0, a0, 0
    srli t0, s0, 2
    add s1, s7, t0
    addi s1, s1, 16
    lw t0, 0(s1)
    beq t0, zero, enemy_chase
    addi s2, t0, -1
    addi a1, s2, 0
    jal ra, move_actor
    beq a0, zero, enemy_detour
    jal zero, enemy_route_clear
enemy_chase:
    lw t0, 0(s0)
    lw t1, 64(zero)
    andi t2, t0, 15
    andi t3, t1, 15
    beq t2, t3, chase_vertical
    sltu t4, t2, t3
    beq t4, zero, chase_left
    addi a1, zero, 1
    jal zero, enemy_move
chase_left:
    addi a1, zero, 3
    jal zero, enemy_move
chase_vertical:
    sltu t4, t0, t1
    beq t4, zero, chase_up
    addi a1, zero, 2
    jal zero, enemy_move
chase_up:
    addi a1, zero, 0
enemy_move:
    addi a0, s0, 0
    jal ra, move_actor
    bne a0, zero, enemy_route_clear
    lw s2, 4(s0)
    addi t0, s2, 1
    sw t0, 0(s1)
enemy_detour:
    # Shoot the blocked lane (to break bricks), then follow its edge.
    # Retry the original direction on later actions until clear of the wall.
    addi a0, s0, 0
    jal ra, fire_actor
    addi a1, s2, 1
    andi a1, a1, 3
    addi a0, s0, 0
    jal ra, move_actor
    bne a0, zero, enemy_return
    addi a1, s2, 3
    andi a1, a1, 3
    addi a0, s0, 0
    jal ra, move_actor
    jal zero, enemy_return
enemy_route_clear:
    sw zero, 0(s1)
enemy_shoot:
    addi a0, s0, 0
    jal ra, fire_actor
enemy_return:
    lw s2, 0(sp)
    lw s1, 4(sp)
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)

# Reuse the two enemy slots for reserve waves. Defer if a spawn is occupied.
# a0=enemy record, a1=spawn; no calls, no saved-register side effects.
spawn_reserve:
    lw t0, 56(zero)
    beq t0, zero, spawn_done
    lw t1, 8(a0)
    bne t1, zero, spawn_done
    lw t1, 64(zero)
    beq t1, a1, spawn_done
    addi t3, zero, 80
spawn_actor_scan:
    beq t3, a0, spawn_actor_next
    lw t1, 8(t3)
    beq t1, zero, spawn_actor_next
    lw t1, 0(t3)
    beq t1, a1, spawn_done
spawn_actor_next:
    addi t3, t3, 16
    addi t1, zero, 128
    bne t3, t1, spawn_actor_scan
spawn_activate:
    sw a1, 0(a0)
    addi t1, zero, 2
    sw t1, 4(a0)
    addi t1, zero, 1
    sw t1, 8(a0)
    # Alternate normal (1 HP) and elite (3 HP) by wave index.
    lw t1, 52(zero)
    lw t2, 56(zero)
    sub t1, t1, t2
    andi t1, t1, 1
    bne t1, zero, spawn_normal
    addi t1, zero, 3
    jal zero, spawn_health_ready
spawn_normal:
    addi t1, zero, 1
spawn_health_ready:
    srli t4, a0, 2
    add t4, t4, s7
    sw t1, -8(t4)
    addi t2, zero, 24
    add t2, t2, t4
    sw t1, 0(t2)
    sw zero, 16(t4)
    addi t0, t0, -1
    sw t0, 56(zero)
spawn_done:
    jalr zero, 0(ra)

game_tick:
    addi sp, sp, -16
    sw ra, 12(sp)
    lw t0, 12(zero)
    addi t0, t0, 1
    sw t0, 12(zero)
    lw t0, 36(zero)
    beq t0, zero, tick_bullets
    addi t0, t0, -1
    sw t0, 36(zero)
tick_bullets:
    sw zero, 240(zero)
    sw zero, 244(zero)
    sw zero, 248(zero)
    sw zero, 252(zero)
    lw t0, 28(s7)
    addi t0, t0, 1
    sw t0, 28(s7)
    lw t1, 20(s11)
    andi t1, t1, 3
    bne t1, zero, bullet_period_valid
    addi t1, zero, 2
bullet_period_valid:
    sltu t1, t0, t1
    bne t1, zero, tick_after_bullets
    sw zero, 28(s7)
    jal ra, update_bullets
tick_after_bullets:
    lw t0, 0(zero)
    addi t1, zero, 1
    bne t0, t1, tick_done
    lw t0, 60(zero)
    addi t0, t0, 1
    sw t0, 60(zero)
    lw t1, 48(zero)
    addi t2, zero, 4
    sub t1, t2, t1
    sltu t1, t0, t1
    bne t1, zero, tick_done
    sw zero, 60(zero)
    addi a0, zero, 80
    addi a1, zero, 55
    jal ra, spawn_reserve
    addi a0, zero, 96
    addi a1, zero, 60
    jal ra, spawn_reserve
    addi a0, zero, 112
    addi a1, zero, 75
    jal ra, spawn_reserve
    lw t0, 88(zero)
    beq t0, zero, tick_enemy_two
    addi a0, zero, 80
    jal ra, enemy_ai
tick_enemy_two:
    lw t0, 104(zero)
    beq t0, zero, tick_done
    addi a0, zero, 96
    jal ra, enemy_ai
    lw t0, 120(zero)
    beq t0, zero, tick_done
    addi a0, zero, 112
    jal ra, enemy_ai
tick_done:
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)

# a0=position, a1=4-bit sprite ID. LUT avoids unsupported variable shifts.
draw_tile:
    andi t0, a0, 7
    slli t0, t0, 4
    add t1, t0, a1
    slli t1, t1, 2
    addi t1, t1, 1280
    lw t1, 0(t1)
    addi t0, t0, 15
    slli t0, t0, 2
    addi t0, t0, 1280
    lw t2, 0(t0)
    xori t2, t2, -1
    srli t0, a0, 3
    slli t0, t0, 2
    addi t3, zero, 1024
    slli t3, t3, 1
    add t0, t0, t3
    lw t3, 0(t0)
    and t3, t3, t2
    or t3, t3, t1
    sw t3, 0(t0)
    jalr zero, 0(ra)

render:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    sw s1, 4(sp)
    sw s2, 0(sp)
    lw t0, 44(zero)
    beq t0, zero, restore_entities
    sw zero, 44(zero)
    addi s0, zero, 256
    addi s1, zero, 1024
    slli s1, s1, 1
    addi s2, zero, 32
render_group:
    addi t0, s0, 28
    addi t1, zero, 8
    addi t2, zero, 0
render_pack:
    slli t2, t2, 4
    lw t3, 0(t0)
    or t2, t2, t3
    addi t0, t0, -4
    addi t1, t1, -1
    bne t1, zero, render_pack
    sw t2, 0(s1)
    addi s0, s0, 32
    addi s1, s1, 4
    addi s2, s2, -1
    bne s2, zero, render_group
    jal zero, render_entities
restore_entities:
    addi s0, zero, 192
    addi s1, zero, 8
restore_cell:
    lw a0, 0(s0)
    addi t0, zero, -1
    beq a0, t0, restore_next
    slli t0, a0, 2
    addi t0, t0, 256
    lw a1, 0(t0)
    jal ra, draw_tile
restore_next:
    addi s0, s0, 4
    addi s1, s1, -1
    bne s1, zero, restore_cell
render_entities:
    addi s0, zero, 128
render_bullets:
    lw t0, 8(s0)
    beq t0, zero, render_bullet_next
    lw a0, 0(s0)
    addi a1, zero, 12
    lw t0, 12(s0)
    beq t0, zero, render_bullet_draw
    addi a1, zero, 13
render_bullet_draw:
    jal ra, draw_tile
render_bullet_next:
    addi s0, s0, 16
    addi t0, zero, 192
    bne s0, t0, render_bullets
    addi s0, zero, 64
render_tanks:
    lw t0, 8(s0)
    beq t0, zero, render_tank_next
    lw a0, 0(s0)
    lw a1, 4(s0)
    addi t0, zero, 64
    beq s0, t0, render_player
    addi a1, a1, 8
    jal zero, render_tank_draw
render_player:
    addi a1, a1, 4
render_tank_draw:
    jal ra, draw_tile
render_tank_next:
    addi s0, s0, 16
    addi t0, zero, 128
    bne s0, t0, render_tanks
    lw t0, 8(zero)
    bne t0, zero, render_hud
    lw a0, 64(zero)
    addi a1, zero, 15
    jal ra, draw_tile
render_hud:
    addi t0, zero, 128
    addi t1, zero, 192
    addi t2, zero, 4
cache_bullets:
    addi t3, zero, -1
    lw t4, 8(t0)
    beq t4, zero, cache_bullet_store
    lw t3, 0(t0)
cache_bullet_store:
    sw t3, 0(t1)
    addi t0, t0, 16
    addi t1, t1, 4
    addi t2, t2, -1
    bne t2, zero, cache_bullets
    addi t0, zero, 64
    addi t2, zero, 4
cache_tanks:
    addi t3, zero, -1
    lw t4, 8(t0)
    beq t4, zero, cache_tank_store
    lw t3, 0(t0)
cache_tank_store:
    sw t3, 0(t1)
    addi t0, t0, 16
    addi t1, t1, 4
    addi t2, t2, -1
    bne t2, zero, cache_tanks
    lw t0, 0(zero)
    sw t0, 64(s11)
    lw t0, 4(zero)
    sw t0, 68(s11)
    lw t0, 8(zero)
    sw t0, 72(s11)
    lw t0, 20(zero)
    sw t0, 76(s11)
    lw t0, 24(zero)
    sw t0, 80(s11)
    lw t0, 28(zero)
    sw t0, 84(s11)
    lw t0, 12(zero)
    sw t0, 88(s11)
    lw t0, 32(zero)
    sw t0, 92(s11)
    lw t0, 0(s7)
    sw t0, 100(s11)
    lw t0, 4(s7)
    sw t0, 104(s11)
    lw t0, 8(s7)
    sw t0, 108(s11)
    lw t0, 12(s7)
    sw t0, 112(s11)
    lw t0, 16(s7)
    sw t0, 116(s11)
    lw t0, 24(s7)
    sw t0, 120(s11)
    lw t0, 80(zero)
    sw t0, 124(s11)
    lw t0, 96(zero)
    sw t0, 128(s11)
    lw t0, 96(s11)
    addi t0, t0, 1
    sw t0, 96(s11)
    lw s2, 0(sp)
    lw s1, 4(sp)
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)
