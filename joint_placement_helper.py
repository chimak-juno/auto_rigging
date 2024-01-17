import maya.cmds as mc
import os
import json
import utility as util
import string

LEFT_PREFIX = "l"
RIGHT_PREFIX = "r"
CENTER_PREFIX = "c"
SEPARATOR = "_"
EXTRAT_FINGER_NAME = "extraFinger"
BIND_JNT_SUFFIX = "bnd"
PATH_SLASH = "|"
LABEL_SCALE = 0.1
TOE_OFFSET = 1.25
FINGER_POS_BTW_OFFSET = 3
FINGER_LABEL_SCALE = 0.05
LABEL_OFFSET = [0, 5, 0]
FINGER_LABEL_OFFSET = [0, 2, 0]
FINGER_ROOT_JNT_LIST = ["l_thumb01", "l_index01", "l_middle01", "l_ring01", "l_pinky01"]
LABEL_CUV_ATTR_NAME = "__labelCuv__"


TEMP_SKELETON_JSON_NAME = "template_skeleton"
JNT_LABEL_CUVS_JSON_NAME = "joint_label_cuv_lib"

FILE_ERROR_MSG = "Missing template file!"

class JointPlacementHelper:
    def __init__(self):
        self.jnt_info_dict = json.loads(self.get_json(file_name=TEMP_SKELETON_JSON_NAME))
        self.jnt_label_cuv_dict = json.loads(self.get_json(file_name=JNT_LABEL_CUVS_JSON_NAME))

        self.node_info_dict = {}
        self.label_cuv_list = []
        self.temp_grp = ""
        self.extra_finger_chain_list = None

    def get_json(self, file_name):
        folder_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(folder_path, file_name)
        try:
            file_obj = open(file_path, "r")
            file_content = file_obj.read()
            file_obj.close()
            return file_content
        except IOError:
            mc.warning(FILE_ERROR_MSG)
            return None      
        
    def create_temp_skeleton(self, character_name="demo", finger_count=5, toe_count=0, symmetry=True):
        """
        Create a template skeleton for joint placement.
        """
        self.temp_grp = character_name

        self.temp_grp = mc.group(name=self.temp_grp, empty=True, world=True)
        self.temp_grp = mc.rename(self.temp_grp, util.clear_path(self.temp_grp).replace(SEPARATOR, ""))

        # Handle extra finger
        if finger_count > 5:
            self.extra_finger_chain_list = self.handle_extra_finger(extra_finger_count=finger_count-5)
        elif finger_count < 5:
            fingers_to_delete = ["index", "thumb", "middle", "ring", "pinky"][finger_count:]

            for jnt_key in self.jnt_info_dict.keys():
                for finger_str in fingers_to_delete:
                    if finger_str in jnt_key:
                        self.jnt_info_dict.pop(jnt_key)
                        # Remove related label in label dictionary as well
                        if (LEFT_PREFIX+SEPARATOR in jnt_key) and ("01" in jnt_key):
                            self.jnt_label_cuv_dict.pop(jnt_key)

        # Handle toes:
        self.handle_toe(toe_count=toe_count)

        # Create joints based on the joint dictionary
        for jnt_key, jnt_info in self.jnt_info_dict.items():
            jnt_name = SEPARATOR.join([self.temp_grp, jnt_key])
            jnt_pos = jnt_info["pos"]

            mc.select(deselect=True)
            jnt_name = mc.joint(name=jnt_name, position=jnt_pos)
            jnt_name = mc.parent(jnt_name, self.temp_grp)[0]

            jnt_info["jnt_name"] = jnt_name
            jnt_info["uuid"] = self.get_uuid(jnt_name)

        # Connect all the joints by parenting them to their parent joints.
        for jnt_key, jnt_obj in self.jnt_info_dict.items():
            if jnt_obj["parent"] is not None:
                mc.parent(self.get_jnt_name(jnt_key), self.get_jnt_name(jnt_obj["parent"]))

        # Connect the right side joints to left side joints by using multiply divide node,
        # in order to make the right joints a mirror image to left joints

        left_side_jnt_key_list = []

        for jnt_key, jnt_info in self.jnt_info_dict.items():
            side_prefix = self.get_jnt_name(jnt_key).split(SEPARATOR)[-2]
            if side_prefix == LEFT_PREFIX:
                left_side_jnt_key_list.append(jnt_key)

        if symmetry is True:
            for jnt_key in left_side_jnt_key_list:
                left_jnt_name = self.get_jnt_name(jnt_key)
                right_jnt_name = self.get_jnt_name(jnt_key.replace(LEFT_PREFIX+SEPARATOR, RIGHT_PREFIX+SEPARATOR))

                md_rotate_node = mc.createNode("multiplyDivide", name=left_jnt_name+"_mdRotateNode")
                self.node_info_dict[md_rotate_node] = self.get_uuid(md_rotate_node)
                md_trans_node = mc.createNode("multiplyDivide", name=left_jnt_name + "_mdTransNode")
                self.node_info_dict[md_trans_node] = self.get_uuid(md_trans_node)

                mc.setAttr(md_rotate_node+ ".input2X", 1)
                mc.setAttr(md_rotate_node + ".input2Y", -1)
                mc.setAttr(md_rotate_node + ".input2Z", -1)
                mc.setAttr(md_rotate_node + ".operation", 1)

                mc.setAttr(md_trans_node + ".input2X", -1)
                mc.setAttr(md_trans_node + ".input2Y", 1)
                mc.setAttr(md_trans_node + ".input2Z", 1)
                mc.setAttr(md_trans_node + ".operation", 1)

                mc.connectAttr(left_jnt_name + ".translate", md_trans_node+".input1")
                mc.connectAttr(left_jnt_name + ".rotate", md_rotate_node + ".input1")
                mc.connectAttr(md_trans_node + ".output",  right_jnt_name+".translate")
                mc.connectAttr(md_rotate_node + ".output", right_jnt_name + ".rotate")

                # Lock the translation and rotation of right-hand side joints.

                mc.setAttr(right_jnt_name + ".translate", lock=True)
                mc.setAttr(right_jnt_name + ".rotate", lock=True)
                mc.setAttr(right_jnt_name + ".scale", lock=True)

        self.create_jnt_label()

    def handle_extra_finger(self, extra_finger_count):
        alphabet_list = string.ascii_uppercase
        extra_finger_chain_list = []
        for i in range(extra_finger_count):
            for prefix in [LEFT_PREFIX, RIGHT_PREFIX]:
                extra_finger_chain = []
                parent_jnt_key = prefix + SEPARATOR + "wrist"
                for finger_seq in range(4):
                    pinky_jnt_pos = self.jnt_info_dict[prefix + SEPARATOR + "pinky" + str((finger_seq+1)).zfill(2)]["pos"]
                    finger_jnt_key = prefix + SEPARATOR + EXTRAT_FINGER_NAME + alphabet_list[i] + str((finger_seq+1)).zfill(2)

                    jnt_info = {}
                    jnt_info["jnt_name"] = finger_jnt_key
                    jnt_info["parent"] = parent_jnt_key
                    jnt_info["pos"] = [pinky_jnt_pos[0], pinky_jnt_pos[1], pinky_jnt_pos[2] - FINGER_POS_BTW_OFFSET*(i+1)]
                    self.jnt_info_dict[finger_jnt_key] = jnt_info

                    extra_finger_chain.append(finger_jnt_key)

                    parent_jnt_key = finger_jnt_key
                extra_finger_chain_list.append(extra_finger_chain)

        return extra_finger_chain_list

    def create_jnt_label(self):
        """
        Create the joint label curves based on the global label information dictionary
        """
        for jnt_key, label_cuvs_info in self.jnt_label_cuv_dict.items():
            cuv_grp = mc.group(name=self.jnt_info_dict[jnt_key]["jnt_name"]+"Label"+SEPARATOR+"cuv", empty=True)

            if jnt_key in FINGER_ROOT_JNT_LIST:
                label_scale = FINGER_LABEL_SCALE
                label_offset = FINGER_LABEL_OFFSET
            else:
                label_scale = LABEL_SCALE
                label_offset = LABEL_OFFSET

            for single_cuv_obj in label_cuvs_info:
                new_cuv = mc.curve(point=single_cuv_obj["point"], degree=single_cuv_obj["degree"])
                closed_cuv = mc.closeCurve(new_cuv, caching=False)
                mc.delete(new_cuv)
                cuv_shape_node = mc.ls(mc.listRelatives(closed_cuv), type="nurbsCurve")
                mc.parent(cuv_shape_node, cuv_grp, shape=True, relative=True)
                mc.delete(closed_cuv)

            # Move all the labels curves to the right places, constraint to their joint and lock the translation, rotation and scale
            mc.xform(cuv_grp, centerPivots=True)
            mc.scale(label_scale, label_scale, label_scale, cuv_grp)
            mc.pointConstraint(self.get_jnt_name(jnt_key), cuv_grp, offset=label_offset)

            cuv_grp = mc.parent(cuv_grp, self.temp_grp)[0]
            mc.setAttr(cuv_grp+".translate", lock=True)
            mc.setAttr(cuv_grp+".rotate", lock=True)
            mc.setAttr(cuv_grp+".scale", lock=True)

            self.label_cuv_list.append(cuv_grp)

    def finish_jnt_placement(self):
        """
        Clean up the scene after joint placement. Rename all the joint(from template joint to bind joint), zero out the rotation,
        return a new bind joint info dictionary.
        """
        #self.temp_grp = mc.listRelatives(self.get_jnt_name("c_root"), parent=True, path=True)[0]

        # Delete all the label cuvs
        for label_cuv in self.label_cuv_list:
            mc.delete(label_cuv)

        # Delete all the node created for the template skeleton
        for node_name in self.node_info_dict.keys():
            mc.delete(node_name)

        for jnt_key, jnt_info in self.jnt_info_dict.items():
            if jnt_key != "c_root":
                jnt_name = self.get_jnt_name(jnt_key)
                mc.setAttr(jnt_name + ".translate", lock=False)
                mc.setAttr(jnt_name + ".rotate", lock=False)
                mc.setAttr(jnt_name + ".scale", lock=False)
                mc.parent(jnt_name, self.temp_grp)

        bind_jnt_dict = {}

        # add joint info to the bind joint dict
        for jnt_key, jnt_info in self.jnt_info_dict.items():
            old_jnt_name = self.get_jnt_name(jnt_key)
            bind_jnt_name = old_jnt_name.split(PATH_SLASH)[-1] + SEPARATOR + BIND_JNT_SUFFIX
            mc.makeIdentity(old_jnt_name, rotate=True, jointOrient=True, apply=True)
            bind_jnt_name = mc.rename(old_jnt_name, bind_jnt_name)

            bind_jnt_info = {}
            bind_jnt_info["uuid"] = jnt_info["uuid"]
            if jnt_info["parent"] is not None:
                bind_jnt_info["parent_uuid"] = self.jnt_info_dict[jnt_info["parent"]]["uuid"]
            else:
                bind_jnt_info["parent_uuid"] = None
            bind_jnt_dict[jnt_key] = bind_jnt_info



        # Chest joint will be replaced by the second last spine joint, so delete it here
        mc.delete(mc.ls(bind_jnt_dict["c_chest"]["uuid"]))
        bind_jnt_dict["l_clavicle"]["parent_uuid"] = None
        bind_jnt_dict["r_clavicle"]["parent_uuid"] = None
        bind_jnt_dict["c_neck"]["parent_uuid"] = None
        bind_jnt_dict.pop("c_chest")

        return self.temp_grp, bind_jnt_dict

    def handle_toe(self, toe_count):
        if toe_count > 0:
            alphhabet_list = string.ascii_uppercase
            for i in range(toe_count):
                for suffix in [LEFT_PREFIX, RIGHT_PREFIX]:
                    for name in ["toeTemp01", "toeTemp02", "toeTemp03"]:
                        template_jnt_info = self.jnt_info_dict[suffix+SEPARATOR+name]
                        jnt_info = {}
                        jnt_key = template_jnt_info["jnt_name"].replace("toeTemp", "toe"+alphhabet_list[i])
                        jnt_info["jnt_name"] = jnt_key

                        if name != "toe01":
                            jnt_info["parent"] = template_jnt_info["parent"].replace("toeTemp", "toe" + alphhabet_list[i])
                        else:
                            jnt_info["parent"] = template_jnt_info["parent"]

                        if i%2 == 0:
                            diff = (i+1)*TOE_OFFSET
                        else:
                            diff = -(i+1)*TOE_OFFSET
                        temp_pos = template_jnt_info["pos"]
                        jnt_info["pos"] = [temp_pos[0]+diff, temp_pos[1], temp_pos[2]]

                        self.jnt_info_dict[jnt_key] = jnt_info

        for jnt_key in self.jnt_info_dict.keys():
            if "toeTemp" in jnt_key:
                self.jnt_info_dict.pop(jnt_key)

    def get_uuid(self, obj_name):
        """
        Get the object uuid.
        """
        uuid = mc.ls(obj_name, uuid=True)[0]
        return uuid

    def get_jnt_name(self, jnt_key):
        """
        Get the joint name by the joint key
        """
        jnt_uuid = self.jnt_info_dict[jnt_key]["uuid"]
        return mc.ls(jnt_uuid)[0]

    def has_attr(self, obj_name, attr_name):
        """
        To check the object if it has the specific attribute.
        """
        for attr in mc.listAttr(obj_name):
            if attr == attr_name:
                return True
        return False








