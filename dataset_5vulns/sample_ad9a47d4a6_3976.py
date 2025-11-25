#!/usr/bin/python

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
import procgame.game, sys, os
import procgame.config
import random
import procgame.sound

sys.path.insert(0,os.path.pardir)
import bingo_emulator.common.units as units
import bingo_emulator.common.functions as functions
from bingo_emulator.graphics import methods as graphics
from bingo_emulator.graphics.spelling_bee import *

class MulticardBingo(procgame.game.Mode):
    def __init__(self, game):
        super(MulticardBingo, self).__init__(game=game, priority=5)
        self.holes = []
        self.startup()
        self.game.sound.register_music('motor', "audio/woodrail_motor.wav")
        self.game.sound.register_music('search1', "audio/automatic_search_one_ball.wav")
        self.game.sound.register_music('search2', "audio/automatic_search_two_ball.wav")
        self.game.sound.register_music('search3', "audio/automatic_search_three_ball.wav")
        self.game.sound.register_music('search4', "audio/automatic_search_four_ball.wav")
        self.game.sound.register_music('search5', "audio/automatic_search_five_ball.wav")
        self.game.sound.register_music('search6', "audio/automatic_search_six_ball.wav")
        self.game.sound.register_music('search7', "audio/automatic_search_seven_ball.wav")
        self.game.sound.register_music('search8', "audio/automatic_search_eight_ball.wav")
        self.game.sound.register_sound('add', "audio/woodrail_coin.wav")
        self.game.sound.register_sound('tilt', "audio/tilt.wav")
        self.game.sound.register_sound('step', "audio/step.wav")

    def sw_coin_active(self, sw):
        self.game.tilt.disengage()
        self.regular_play()
        self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_startButton_active(self, sw):
        if self.game.replays > 0 or self.game.switches.freeplay.is_active():
            self.game.tilt.disengage()
            self.regular_play()

    def sw_trough4_active_for_1s(self, sw):
        if self.game.ball_count.position >= 4:
            self.timeout_actions()
    
    def timeout_actions(self):
        if (self.game.timer.position < 39):
            self.game.timer.step()
            self.delay(name="timeout", delay=5.0, handler=self.timeout_actions)
        else:
            self.game.timer.step()
            self.tilt_actions()

    def sw_trough8_closed(self, sw):
        if self.game.start.status == False:
            self.game.ball_count.position -= 1
            self.game.returned = True
            self.check_lifter_status()
        else:
            self.check_lifter_status()

    def sw_enter_active(self, sw):
        if self.game.switches.left.is_active() and self.game.switches.right.is_active():
            self.game.end_run_loop()
            os.system(f"/home/nbaldridge/proc/bingo_emulator/start_game.sh {self.game.name}")

    def check_shutter(self, start=0):
        if start == 1:
            if self.game.switches.smRunout.is_active():
                if self.game.switches.shutter.is_active():
                    self.game.coils.shutter.disable()
        else:
            if self.game.switches.shutter.is_inactive():
                if self.game.switches.smRunout.is_active():
                    self.game.coils.shutter.disable()

    def regular_play(self):
        self.holes = []
        self.cancel_delayed(name="search")
        self.cancel_delayed(name="card1_replay_step_up")
        self.cancel_delayed(name="card2_replay_step_up")
        self.cancel_delayed(name="card3_replay_step_up")
        self.cancel_delayed(name="card4_replay_step_up")
        self.cancel_delayed(name="timeout")
        self.game.search_index.disengage()
        self.game.coils.counter.pulse()
        self.game.returned = False
        self.game.sound.stop('add')
        self.game.sound.play('add')
        if self.game.start.status == True:
            if self.game.selector.position <= 3:
                self.game.selector.step()
            if self.game.switches.shutter.is_inactive():
                self.game.coils.shutter.enable()
            self.replay_step_down()
            self.check_lifter_status()
        else:
            self.game.start.engage(self.game)
            self.game.card1_replay_counter.reset()
            self.game.card2_replay_counter.reset()
            self.game.card3_replay_counter.reset()
            self.game.card4_replay_counter.reset()
            self.game.average.disengage()
            self.game.good.disengage()
            self.game.expert.disengage()
            self.game.average.engage(self.game)
            self.game.selector.reset()
            self.game.ball_count.reset()
            self.game.timer.reset()
            self.game.sound.play_music('motor', -1)
            self.regular_play()
        self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)
        self.game.tilt.disengage()

    def check_lifter_status(self):
        if self.game.tilt.status == False:
            if self.game.switches.trough8.is_closed() and self.game.switches.trough5.is_open() and self.game.switches.trough4.is_open() and self.game.switches.trough3.is_closed() and self.game.switches.trough2.is_closed():
                if self.game.switches.shooter.is_open():
                    self.game.coils.lifter.enable()
                    self.game.returned = False
            else:
                if self.game.start.status == False:
                    if self.game.switches.trough4.is_open():
                        if self.game.switches.shooter.is_open():
                            if self.game.switches.gate.is_closed():
                                self.game.coils.lifter.enable()
                    else:
                        if self.game.returned == True and self.game.ball_count.position == 4:
                            if self.game.switches.shooter.is_open():
                                self.game.coils.lifter.enable()
                                self.game.returned = False

    def sw_smRunout_active_for_1ms(self, sw):
        if self.game.start.status == True:
            self.check_shutter(1)
        else:
            self.check_shutter()

    def sw_trough1_closed(self, sw):
        if self.game.switches.shooter.is_closed():
            self.game.coils.lifter.disable()

    def sw_ballLift_active_for_500ms(self, sw):
        if self.game.tilt.status == False:
            if self.game.switches.shooter.is_open():
                if self.game.ball_count.position < 5:
                    self.game.coils.lifter.enable()

    def sw_gate_inactive_for_1ms(self, sw):
        self.game.start.disengage()
        if self.game.switches.shutter.is_active():
            self.game.coils.shutter.enable()
        self.game.ball_count.step()
        if self.game.ball_count.position >= 4:
            if self.game.search_index.status == False:
                self.search()
        if self.game.ball_count.position <= 4:
            self.check_lifter_status()

    def sw_hole1_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(1)
            if self.game.good.status == True:
                self.game.average.disengage()
                self.game.good.disengage()
                self.game.expert.engage(self.game)
            else:
                self.game.average.disengage()
                self.game.good.engage(self.game)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole2_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(2)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole3_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(3)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole4_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(4)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole5_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(5)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole6_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(6)
            if self.game.good.status == True:
                self.game.average.disengage()
                self.game.good.disengage()
                self.game.expert.engage(self.game)
            else:
                self.game.average.disengage()
                self.game.good.engage(self.game)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole7_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(7)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole8_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(8)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole9_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(9)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole10_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(10)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole11_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(11)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole12_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(12)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole13_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(13)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole14_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(14)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole15_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(15)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole16_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(16)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole17_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(17)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_hole18_active_for_40ms(self, sw):
        if self.game.tilt.status == False and self.game.start.status == False:
            self.holes.append(18)
            if self.game.ball_count.position >= 4:
                if self.game.search_index.status == False:
                    self.search()
            self.search_sounds()
            self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def sw_replayReset_active(self, sw):
        self.game.anti_cheat.disengage()
        self.holes = []
        graphics.spelling_bee.display(self)
        self.tilt_actions()
        self.replay_step_down(self.game.replays)

    def tilt_actions(self):
        self.game.start.disengage()
        self.cancel_delayed(name="replay_reset")
        self.cancel_delayed(name="card1_replay_step_up")
        self.cancel_delayed(name="card2_replay_step_up")
        self.cancel_delayed(name="card3_replay_step_up")
        self.cancel_delayed(name="card4_replay_step_up")
        self.cancel_delayed(name="timeout")
        self.game.search_index.disengage()
        if self.game.ball_count.position == 0:
            if self.game.switches.shutter.is_active():
                self.game.coils.shutter.enable()
        self.holes = []
        self.game.selector.reset()
        self.game.ball_count.reset()
        self.game.anti_cheat.engage(self.game)
        self.game.tilt.engage(self.game)
        self.game.average.disengage()
        self.game.good.disengage()
        self.game.expert.disengage()
        self.game.sound.stop_music()
        self.game.sound.play('tilt')
        self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)

    def search_sounds(self):
        self.game.sound.stop_music()
        if self.game.ball_count.position == 1:
            self.game.sound.play_music('search1', -1)
        if self.game.ball_count.position == 2:
            self.game.sound.play_music('search2', -1)
        if self.game.ball_count.position == 3:
            self.game.sound.play_music('search3', -1)
        if self.game.ball_count.position == 4:
            self.game.sound.play_music('search4', -1)
        if self.game.ball_count.position == 5:
            self.game.sound.play_music('search5', -1)
        if self.game.ball_count.position == 6:
            self.game.sound.play_music('search6', -1)
        if self.game.ball_count.position == 7:
            self.game.sound.play_music('search7', -1)
        if self.game.ball_count.position == 8:
            self.game.sound.play_music('search8', -1)

    def sw_tilt_active(self, sw):
        if self.game.tilt.status == False:
            self.tilt_actions()

    def replay_step_down(self, number=0):
        if number > 0:
            if number > 1:
                self.game.replays -= 1
                graphics.replay_step_down(self.game.replays, graphics.spelling_bee.reel1, graphics.spelling_bee.reel10, graphics.spelling_bee.reel100)
                self.game.coils.registerDown.pulse()
                number -= 1
                graphics.spelling_bee.display(self)
                self.delay(name="replay_reset", delay=0.13, handler=self.replay_step_down, param=number)
            elif number == 1:
                self.game.replays -= 1
                graphics.replay_step_down(self.game.replays, graphics.spelling_bee.reel1, graphics.spelling_bee.reel10, graphics.spelling_bee.reel100)
                self.game.coils.registerDown.pulse()
                number -= 1
                graphics.spelling_bee.display(self)
                self.cancel_delayed(name="replay_reset")
        else: 
            if self.game.replays > 0:
                self.game.replays -= 1
                graphics.replay_step_down(self.game.replays, graphics.spelling_bee.reel1, graphics.spelling_bee.reel10, graphics.spelling_bee.reel100)
                self.delay(name="display", delay=0.1, handler=graphics.spelling_bee.display, param=self)
            self.game.coils.registerDown.pulse()

    def replay_step_up(self):
        if self.game.replays < 99:
            self.game.replays += 1
            graphics.replay_step_up(self.game.replays, graphics.spelling_bee.reel1, graphics.spelling_bee.reel10, graphics.spelling_bee.reel100)
        self.game.coils.registerUp.pulse()
        graphics.spelling_bee.display(self)
 
    def search(self):
        for i in range(0, 100):
            if i <= 50:
                self.r = self.closed_search_relays(self.game.searchdisc.position)
                self.game.searchdisc.spin()
            if i >= 51:
                self.r = self.closed_search_relays(self.game.searchdisc2.position + 50)
                self.game.searchdisc2.spin()
            self.wipers = self.r[0]
            self.card = self.r[1]
            self.four = self.r[2]

            self.match = []
            for key in self.wipers:
                for number in self.holes:
                    if number == key:
                        self.match.append(self.wipers[key])
                        relays = sorted(set(self.match))
                        s = functions.count_seq(relays)
                        if self.game.selector.position >= self.card:
                            if s >= 3:
                                self.find_winner(s, self.card, self.four)
                                break
        

    def find_winner(self, relays, card, four):
        if self.game.search_index.status == False and self.game.replays < 99:
            if card == 1:
                if relays == 3 and not four:
                    amount = 2
                    if self.game.good.status == True:
                        amount = 3
                    if self.game.expert.status == True:
                        amount = 16
                    if self.game.card1_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card1_replay_step_up(amount - self.game.card1_replay_counter.position)
                if relays == 4:
                    amount = 8
                    if self.game.good.status == True:
                        amount = 12
                    if self.game.card1_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card1_replay_step_up(amount - self.game.card1_replay_counter.position)
            if card == 2:
                if relays == 3 and not four:
                    amount = 2
                    if self.game.good.status == True:
                        amount = 3
                    if self.game.expert.status == True:
                        amount = 16
                    if self.game.card2_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card2_replay_step_up(amount - self.game.card2_replay_counter.position)
                if relays == 4:
                    amount = 8
                    if self.game.good.status == True:
                        amount = 12
                    if self.game.card2_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card2_replay_step_up(amount - self.game.card2_replay_counter.position)
            if card == 3:
                if relays == 3 and not four:
                    amount = 2
                    if self.game.good.status == True:
                        amount = 3
                    if self.game.expert.status == True:
                        amount = 16
                    if self.game.card3_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card3_replay_step_up(amount - self.game.card3_replay_counter.position)
                if relays == 4:
                    amount = 8
                    if self.game.good.status == True:
                        amount = 12
                    if self.game.card3_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card3_replay_step_up(amount - self.game.card3_replay_counter.position)
            if card == 4:
                if relays == 3 and not four:
                    amount = 2
                    if self.game.good.status == True:
                        amount = 3
                    if self.game.expert.status == True:
                        amount = 16
                    if self.game.card4_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card4_replay_step_up(amount - self.game.card4_replay_counter.position)
                if relays == 4:
                    amount = 8
                    if self.game.good.status == True:
                        amount = 12
                    if self.game.card4_replay_counter.position < amount:
                        self.game.search_index.engage(self.game)
                        self.card4_replay_step_up(amount - self.game.card4_replay_counter.position)

    def card1_replay_step_up(self, number):
        self.game.sound.stop_music()
        if number >= 1:
            self.game.card1_replay_counter.step()
            number -= 1
            self.replay_step_up()
            if self.game.replays == 99:
                number = 0
            self.delay(name="card1_replay_step_up", delay=0.1, handler=self.card1_replay_step_up, param=number)
        else:
            self.game.search_index.disengage()
            self.cancel_delayed(name="card1_replay_step_up")
            self.search_sounds()
            self.search()

    def card2_replay_step_up(self, number):
        self.game.sound.stop_music()
        if number >= 1:
            self.game.card2_replay_counter.step()
            number -= 1
            self.replay_step_up()
            if self.game.replays == 99:
                number = 0
            self.delay(name="card2_replay_step_up", delay=0.1, handler=self.card2_replay_step_up, param=number)
        else:
            self.game.search_index.disengage()
            self.cancel_delayed(name="card2_replay_step_up")
            self.search_sounds()
            self.search()

    def card3_replay_step_up(self, number):
        self.game.sound.stop_music()
        if number >= 1:
            self.game.card3_replay_counter.step()
            number -= 1
            self.replay_step_up()
            if self.game.replays == 99:
                number = 0
            self.delay(name="card3_replay_step_up", delay=0.1, handler=self.card3_replay_step_up, param=number)
        else:
            self.game.search_index.disengage()
            self.cancel_delayed(name="card3_replay_step_up")
            self.search_sounds()
            self.search()

    def card4_replay_step_up(self, number):
        self.game.sound.stop_music()
        if number >= 1:
            self.game.card4_replay_counter.step()
            number -= 1
            self.replay_step_up()
            if self.game.replays == 99:
                number = 0
            self.delay(name="card4_replay_step_up", delay=0.1, handler=self.card4_replay_step_up, param=number)
        else:
            self.game.search_index.disengage()
            self.cancel_delayed(name="card4_replay_step_up")
            self.search_sounds()
            self.search()

    def closed_search_relays(self, rivets):
        self.pos = {}
        self.pos[0] = {}
        self.pos[1] = {2:1, 3:2, 7:3}
        self.pos[2] = {18:1, 2:2, 15:3}
        self.pos[3] = {2:1, 10:2, 5:3}
        self.pos[4] = {17:1, 2:2, 3:3}
        self.pos[5] = {8:1, 2:2, 15:3, 11:4}
        self.pos[6] = {9:1, 2:2, 16:3, 14:4}
        self.pos[7] = {3:1, 13:2, 2:3, 15:4}
        self.pos[8] = {17:1, 2:2, 14:3, 7:4}
        self.pos[9] = {8:1, 2:2, 17:3, 7:4}
        self.pos[10] = {16:1, 13:2, 18:3, 12:4}
        self.pos[11] = {4:1, 13:2, 14:3, 7:4}
        self.pos[12] = {3:1, 2:2, 17:3, 7:4}
        self.pos[13] = {}
        self.pos[14] = {}
        self.pos[15] = {}
        self.pos[16] = {}
        self.pos[17] = {}

        self.pos[18] = {3:1, 10:2, 12:3}
        self.pos[19] = {13:1, 15:2, 7:3}
        self.pos[20] = {16:1, 2:2, 18:3}
        self.pos[21] = {8:1, 10:2, 15:3}
        self.pos[22] = {17:1, 9:2, 7:3, 12:4}
        self.pos[23] = {15:1, 13:2, 5:3, 7:4}
        self.pos[24] = {16:1, 10:2, 15:3, 7:4}
        self.pos[25] = {11:1, 2:2, 5:3, 7:4}
        self.pos[26] = {4:1, 2:2, 15:3, 17:4}
        self.pos[27] = {9:1, 10:2, 5:3, 7:4}
        self.pos[28] = {15:1, 10:2, 5:3, 7:4}
        self.pos[29] = {14:1, 2:2, 12:3, 17:4}
        self.pos[30] = {}
        self.pos[31] = {}
        self.pos[32] = {}
        self.pos[33] = {}
        self.pos[34] = {}

        self.pos[35] = {9:1, 10:2, 5:3}
        self.pos[36] = {14:1, 2:2, 12:3}
        self.pos[37] = {4:1, 2:2, 3:3}
        self.pos[38] = {3:1, 2:2, 5:3}
        self.pos[39] = {17:1, 13:2, 18:3, 12:4}
        self.pos[40] = {16:1, 14:2, 2:3, 15:4}
        self.pos[41] = {9:1, 2:2, 17:3, 7:4}
        self.pos[42] = {3:1, 13:2, 2:3, 17:4}
        self.pos[43] = {17:1, 9:2, 7:3, 11:4}
        self.pos[44] = {18:1, 2:2, 16:3, 9:4}
        self.pos[45] = {8:1, 2:2, 15:3, 7:4}
        self.pos[46] = {11:1, 2:2, 17:3, 7:4}
        self.pos[47] = {}
        self.pos[48] = {}
        self.pos[49] = {}
        self.pos[50] = {}

        self.pos[51] = {9:1, 10:2, 11:3}
        self.pos[52] = {7:1, 2:2, 15:3}
        self.pos[53] = {16:1, 10:2, 15:3}
        self.pos[54] = {8:1, 13:2, 15:3}
        self.pos[55] = {3:1, 2:2, 15:3, 7:4}
        self.pos[56] = {5:1, 13:2, 12:3, 7:4}
        self.pos[57] = {3:1, 2:2, 5:3, 7:4}
        self.pos[58] = {17:1, 7:2, 12:3, 5:4}
        self.pos[59] = {15:1, 2:2, 12:3, 17:4}
        self.pos[60] = {4:1, 13:2, 5:3, 7:4}
        self.pos[61] = {14:1, 2:2, 15:3, 17:4}
        self.pos[62] = {17:1, 18:2, 10:3, 12:4}
        self.pos[63] = {}
        self.pos[64] = {}
        self.pos[65] = {}
        self.pos[66] = {}
        self.pos[67] = {}

        self.pos[68] = {}
        self.pos[69] = {}
        self.pos[70] = {}
        self.pos[71] = {}
        self.pos[72] = {}
        self.pos[73] = {}
        self.pos[74] = {}
        self.pos[75] = {}
        self.pos[76] = {}
        self.pos[77] = {}
        self.pos[78] = {}
        self.pos[79] = {}
        self.pos[80] = {}
        self.pos[81] = {}
        self.pos[82] = {}
        self.pos[83] = {}
        self.pos[84] = {}

        self.pos[85] = {}
        self.pos[86] = {}
        self.pos[87] = {}
        self.pos[88] = {}
        self.pos[89] = {}
        self.pos[90] = {}
        self.pos[91] = {}
        self.pos[92] = {}
        self.pos[93] = {}
        self.pos[94] = {}
        self.pos[95] = {}
        self.pos[96] = {}
        self.pos[97] = {}
        self.pos[98] = {}
        self.pos[99] = {}
        self.pos[100] = {}

        four = 0

        if rivets in range(0,18):
            card = 1
        if rivets in range(5,13):
            four = 0
        if rivets in range(18,35):
            card = 2
        if rivets in range(22,30):
            four = 0
        if rivets in range(35,50):
            card = 3
        if rivets in range(39,47):
            four = 0
        if rivets in range(50,100):
            card = 4
        if rivets in range(55,62):
            four = 0

        return (self.pos[rivets], card, four)
            
    def startup(self):        
        self.eb = False
        self.tilt_actions()

class SpellingBee(procgame.game.BasicGame):
    """ Spelling Bee was a re-run of Crosswords """
    def __init__(self, machine_type):
        super(SpellingBee, self).__init__(machine_type)
        pygame.mixer.pre_init(44100,-16,2,512)
        self.sound = procgame.sound.SoundController(self)
        self.sound.set_volume(1.0)
        self.trough_count = 6

        self.searchdisc = units.Search("searchdisc", 49)
        self.searchdisc2 = units.Search("searchdisc2", 49)

        self.s1 = units.Relay("s1")
        self.s2 = units.Relay("s2")
        self.s3 = units.Relay("s3")
        self.s4 = units.Relay("s4")
        self.s5 = units.Relay("s5")
        self.search_index = units.Relay("search_index")

        self.card1_replay_counter = units.Stepper("card1_replay_counter", 100)
        self.card2_replay_counter = units.Stepper("card2_replay_counter", 100)
        self.card3_replay_counter = units.Stepper("card3_replay_counter", 100)
        self.card4_replay_counter = units.Stepper("card4_replay_counter", 100)

        self.average = units.Relay("average")
        self.good = units.Relay("good")
        self.expert = units.Relay("expert")

        self.selector = units.Stepper("selector", 4)
        self.timer = units.Stepper("timer", 40)
        self.ball_count = units.Stepper("ball_count", 5)

        self.anti_cheat = units.Relay("anti_cheat")
        self.start = units.Relay("start")
        self.tilt = units.Relay("tilt")

        self.replays = 0
        self.returned = False

    def reset(self):
        super(SpellingBee, self).reset()
        self.logger = logging.getLogger('game')
        self.load_config('bingo.yaml')
        
        main_mode = MulticardBingo(self)
        self.modes.add(main_mode)
        
game = SpellingBee(machine_type='pdb')
game.reset()
game.run_loop()