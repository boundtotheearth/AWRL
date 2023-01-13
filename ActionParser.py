from Game.Action import ActionEnd, ActionMove, ActionMoveCombineLoad, ActionDirectAttack, ActionIndirectAttack, ActionCapture, ActionBuild, ActionRepair, ActionUnload

class ActionParser:
    def parse(self, command):
        try:
            input_params = command.strip().split(" ")
            move_type = input_params[0].lower()

            action = None
            if move_type == "end":
                action = ActionEnd()
            elif move_type == "move":
                #example: move 3,4 uulld
                #Moving on top of a damaged unit of the same type should combine
                #Moving on top of a transport unit should load if possible
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                unit_position = (source_r, source_c)

                move_offset = input_params[2].split(",")
                move_offset_r = int(move_offset[0])
                move_offset_c = int(move_offset[1])
                move_offset = (move_offset_r, move_offset_c)

                action = ActionMoveCombineLoad(ActionMove(unit_position=unit_position, offset=move_offset))
            elif move_type == "attack":
                #example: attack 1,2 u
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                unit_position = (source_r, source_c)

                move_offset = input_params[2].split(",")
                move_offset_r = int(move_offset[0])
                move_offset_c = int(move_offset[1])
                move_offset = (move_offset_r, move_offset_c)

                offset = input_params[3].split(",")
                offset_r = int(offset[0])
                offset_c = int(offset[1])
                attack_offset = (offset_r, offset_c)

                distance = abs(offset_r) + abs(offset_c)
                if distance > 1:
                    action = ActionIndirectAttack(unit_position, attack_offset)
                elif distance == 1:
                    action = ActionDirectAttack(ActionMove(unit_position=unit_position, offset=move_offset), attack_offset=attack_offset)
            elif move_type == "capture":
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                unit_position = (source_r, source_c)

                move_offset = input_params[2].split(",")
                move_offset_r = int(move_offset[0])
                move_offset_c = int(move_offset[1])
                move_offset = (move_offset_r, move_offset_c)
                
                action = ActionCapture(ActionMove(unit_position=unit_position, offset=move_offset))
            elif move_type == "repair":
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                unit_position = (source_r, source_c)

                move_offset = input_params[2].split(",")
                move_offset_r = int(move_offset[0])
                move_offset_c = int(move_offset[1])
                move_offset = (move_offset_r, move_offset_c)

                offset = input_params[3].split(",")
                offset_r = int(offset[0])
                offset_c = int(offset[1])
                repair_offset = (offset_r, offset_c)

                action = ActionRepair(ActionMove(unit_position=unit_position, offset=move_offset), repair_offset=repair_offset)
            elif move_type == "build":
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                property_position = (source_r, source_c)

                unit_code = input_params[2]

                action = ActionBuild(property_position, unit_code)
            elif move_type == "unload":
                source = input_params[1].split(",")
                source_r = int(source[0])
                source_c = int(source[1])
                unit_position = (source_r, source_c)

                move_offset = input_params[2].split(",")
                move_offset_r = int(move_offset[0])
                move_offset_c = int(move_offset[1])
                move_offset = (move_offset_r, move_offset_c)

                offset = input_params[3].split(",")
                offset_r = int(offset[0])
                offset_c = int(offset[1])
                unload_offset = (offset_r, offset_c)

                idx = int(input_params[4])

                action = ActionUnload(ActionMove(unit_position=unit_position, offset=move_offset), unload_offset=unload_offset, idx=idx)
            elif move_type == "cop":
                pass
            elif move_type == "scop":
                pass
        except:
            print("Error parsing action!")

        return action