import maya.cmds as mc
import utility as util, joint_placement_helper
import string
reload(util)

MISC_GRP = "mics"
CTR_GRP = "ctr"
BIND_JNT_GRP = "bindSkeleton_grp"
ANIM_JNT_GRP = "animateSkeleton_grp"
LEFT_PREFIX = "l"
RIGHT_PREFIX = "r"
CENTER_PREFIX = "c"
SEPARATOR = util.SEPARATOR
PATH_SLASH ="|"
BIND_JNT_SUFFIX = "bnd"
ANIM_JNT_SUFFIX = "jnt"
INF_JNT_SUFFIX = "inf"
IK_JNT_SUFFIX = "ik"
FK_JNT_SUFFIX = "fk"
NODE_OBJ_SUFFIX = "nod"
FOLLICLE_SUFFIX = "fol"
CONTROL_SUFFIX = "ctr"
CLUSTER_SUFFIX = "cls"
SPACE_GRP_SUFFIX = "nul"
OFFSET_GRP_SUFFIX = "offset"
NURBS_SURF_SUFFIX = "surf"
IK_HANDLE_SUFFIX = "ikh"
GRP_SUFFIX = "grp"
BLEND_COLORS_SUFFIX = "bc"
REVERSE_NODE_SUFFIX = "rev"
LOCATOR_SUFFIX = "loc"
DRIVER_SUFFIX = "drv"
DISTANCE_DIMEN_SUFFIX = "dm"


class AutoRigger:

    def __init__(self, rig_grp, bind_jnt_info_dict):
        self.rig_grp = rig_grp
        self.bind_jnt_info_dict = bind_jnt_info_dict
        self.anim_jnt_info_dict = {}
        self.misc_grp = ""
        self.ctr_grp = ""
        self.bind_jnt_grp = ""
        self.anim_jnt_grp = ""
        self.global_ctr = ""
        self.cog_ctr = ""
        self.l_finger_root_jnt_key = ["l_thumb01", "l_index01", "l_middle01", "l_ring01", "l_pinky01"]
        self.r_finger_root_jnt_key = ["r_thumb01", "r_index01", "r_middle01", "r_ring01", "r_pinky01"]
        self.l_toe_root_jnt_key = []
        self.r_toe_root_jnt_key = []

    def create_rig(self, spine_jnt_count=5, neck_jnt_count=3, upper_arm_twist_count=3, lower_arm_twist_count=3,
                   upper_leg_twist_count=3, lower_leg_twist_count=3, finger_count=5, toe_count=0, mirror_behavior=True,
                   stretch_arm=True, stretch_leg=True, fk_arm=True, ik_arm=True, fk_leg=True, ik_leg=False):
        """
        Main function, coordinating with other functions
        """
        self.misc_grp = mc.group(name=MISC_GRP, empty=True, parent=self.rig_grp)
        self.ctr_grp = mc.group(name=CTR_GRP, empty=True, parent=self.rig_grp)
        self.bind_jnt_grp = mc.group(name=BIND_JNT_GRP, empty=True, parent=self.rig_grp)
        self.anim_jnt_grp = mc.group(name=ANIM_JNT_GRP, empty=True, parent=self.rig_grp)

        prefix = util.clear_path(self.rig_grp)

        # Update finger root jnt list if finger count is not default value
        if finger_count > 5:
            extra_finger_count = finger_count - 5
            self.l_finger_root_jnt_key += self.get_extra_digit(digit_count=extra_finger_count,
                                                               left_or_right=LEFT_PREFIX, name="extraFinger")
            self.r_finger_root_jnt_key += self.get_extra_digit(digit_count=extra_finger_count,
                                                               left_or_right=RIGHT_PREFIX, name="extraFinger")
        elif 5 >= finger_count > 1:
            self.l_finger_root_jnt_key = self.l_finger_root_jnt_key[:finger_count]
            self.r_finger_root_jnt_key = self.r_finger_root_jnt_key[:finger_count]
        else:
            self.l_finger_root_jnt_key = [self.l_finger_root_jnt_key[1]]
            self.r_finger_root_jnt_key = [self.r_finger_root_jnt_key[1]]

        if toe_count > 0:
            self.l_toe_root_jnt_key = self.get_extra_digit(digit_count=toe_count,
                                                           left_or_right=LEFT_PREFIX, name="toe")
            self.r_toe_root_jnt_key = self.get_extra_digit(digit_count=toe_count,
                                                           left_or_right=RIGHT_PREFIX, name="toe")

        self.init_jnt_orientation(mirror_behavior=mirror_behavior)

        # Create spine and neck bind joints
        spine_jnt_key_list = self.create_spine(spine_jnt_count=spine_jnt_count)
        neck_jnt_key_list = self.create_neck(neck_jnt_count=neck_jnt_count)

        mc.parent(self.get_bnd_jnt_name(spine_jnt_key_list[0]), self.get_bnd_jnt_name("c_root"))
        mc.parent(self.get_bnd_jnt_name(neck_jnt_key_list[0]), self.get_bnd_jnt_name(spine_jnt_key_list[-1]))
        spine_bnd_jnt_chain = self.get_bnd_jnt_name(spine_jnt_key_list)
        neck_bnd_jnt_chain = self.get_bnd_jnt_name(neck_jnt_key_list)
        mc.parent(self.get_bnd_jnt_name("l_clavicle"), spine_bnd_jnt_chain[-2])
        mc.parent(self.get_bnd_jnt_name("r_clavicle"), spine_bnd_jnt_chain[-2])

        # Create pelvis bind joint
        self.create_pelvis_jnt()

        # Create anim joints
        self.create_anim_skeleton()

        # Put all bind joints to bind skeleton group
        mc.parent(self.get_bnd_jnt_name("c_root"), self.bind_jnt_grp)

        # Put all anim joints to anim skeleton group
        mc.parent(self.get_anim_jnt_name("c_root"), self.anim_jnt_grp)

        # Create clavicle controls
        l_clavicle_ctr_space, l_clavicle_ctr = self.create_general_ctr(jnt = self.get_anim_jnt_name("l_clavicle"), ctr_type="clavicle",
                                                                       ctr_scale=[7, 7, 7], ctr_move=[0, 10, 0])
        r_clavicle_ctr_space, r_clavicle_ctr = self.create_general_ctr(jnt = self.get_anim_jnt_name("r_clavicle"), ctr_type="clavicle",
                                                                       ctr_scale=[7, 7, 7], ctr_move=[0, 10, 0] , flip_ctr=True)

        # Create neck controls
        neck_ctr_space_list, neck_ctr_list = self.create_neck_ctr(neck_jnt_chain=self.get_anim_jnt_name(neck_jnt_key_list),
                                                                  ctr_scale=[7,7,7])

        # Create twist bind joints
        if upper_arm_twist_count > 0:
            upper_arm_twist_rate = self.get_default_twist_rate(upper_arm_twist_count, counter_twist=True)
            self.create_twist_jnts(self.get_bnd_jnt_name("l_shoulder"), self.get_bnd_jnt_name("l_elbow"),
                                   twist_rate_list=upper_arm_twist_rate)
            self.create_twist_jnts(self.get_bnd_jnt_name("r_shoulder"), self.get_bnd_jnt_name("r_elbow"),
                                   twist_rate_list=upper_arm_twist_rate)

        if lower_arm_twist_count > 0:
            lower_arm_twist_rate = self.get_default_twist_rate(lower_arm_twist_count, counter_twist=False)
            self.create_twist_jnts(self.get_bnd_jnt_name("l_wrist"), self.get_bnd_jnt_name("l_elbow"),
                                   twist_rate_list=lower_arm_twist_rate, parent_to_end_jnt=True)
            self.create_twist_jnts(self.get_bnd_jnt_name("r_wrist"), self.get_bnd_jnt_name("r_elbow"),
                                   twist_rate_list=lower_arm_twist_rate, parent_to_end_jnt=True)

        if upper_leg_twist_count > 0:
            upper_leg_twist_rate = self.get_default_twist_rate(upper_leg_twist_count, counter_twist=True)
            self.create_twist_jnts(self.get_bnd_jnt_name("l_thigh"), self.get_bnd_jnt_name("l_knee"),
                                   twist_rate_list=upper_leg_twist_rate)
            self.create_twist_jnts(self.get_bnd_jnt_name("r_thigh"), self.get_bnd_jnt_name("r_knee"),
                                   twist_rate_list=upper_leg_twist_rate)
        if lower_leg_twist_count > 0:
            lower_leg_twist_rate = self.get_default_twist_rate(lower_leg_twist_count, counter_twist=False)
            self.create_twist_jnts(self.get_bnd_jnt_name("l_ankle"), self.get_bnd_jnt_name("l_knee"), twist_axis="y",
                                   twist_rate_list=lower_leg_twist_rate, parent_to_end_jnt=True)
            self.create_twist_jnts(self.get_bnd_jnt_name("r_ankle"), self.get_bnd_jnt_name("r_knee"), twist_axis="y",
                                   twist_rate_list=lower_leg_twist_rate, parent_to_end_jnt=True)

        # Create global control
        global_ctr_space, self.global_ctr = self.create_general_ctr(ctr_type="circle", ctr_scale=[50, 50, 50], ctr_rot=[0,0,90],
                                                                    mid_name="global")

        # Create COG control
        cog_ctr_space, self.cog_ctr = self.create_general_ctr(jnt=self.get_anim_jnt_name("c_root"), ctr_type="cog",
                                                              ctr_scale=[50, 50, 50], mid_name="cog",
                                                              ctr_move=[0, -5, 0], parent=self.global_ctr)

        # Create hip control
        hip_ctr_space, hip_ctr= self.create_general_ctr(jnt=self.get_anim_jnt_name("c_pelvis"), ctr_type="hip",
                                                        ctr_scale=[20, 20, 15], mid_name="hip",
                                                        ctr_move=[0, -20, 0], parent=self.cog_ctr)

        # Create ribbon spine base on the animate spine joints
        spine_ctr_space_list, spine_ctr_list, spine_fk_ctr_space_list, spine_fk_ctr_list = self.create_ribbon_spine(self.get_anim_jnt_name(spine_jnt_key_list))

        l_clavicle_ctr_space = mc.parent(l_clavicle_ctr_space, spine_ctr_list[-1])[0]
        r_clavicle_ctr_space = mc.parent(r_clavicle_ctr_space, spine_ctr_list[-1])[0]
        neck_ctr_space_list[0] = mc.parent(neck_ctr_space_list[0], spine_ctr_list[-1])[0]
        spine_fk_ctr_space_list[0] = mc.parent(spine_fk_ctr_space_list[0], self.cog_ctr)[0]

        # Create ik arms and legs:
        if ik_arm is True:
            l_ik_arm_chain, l_ik_arm_ctrs_grp, l_ik_arm_ctr, l_ik_arm_hdl = self.create_ik_limb(root_jnt_key="l_shoulder", mid_jnt_key="l_elbow",
                                                                                                end_jnt_key="l_wrist", main_name="arm",
                                                                                                match_jnt_orient=True, ik_ctr_rotate=[0,0,90],
                                                                                                pv_ctr_rotate=[90,0,0])
            r_ik_arm_chain, r_ik_arm_ctrs_grp, r_ik_arm_ctr, r_ik_arm_hdl = self.create_ik_limb(root_jnt_key="r_shoulder", mid_jnt_key="r_elbow",
                                                                                                end_jnt_key="r_wrist", main_name="arm",
                                                                                                match_jnt_orient=True, ik_ctr_rotate=[0,0,90],
                                                                                                pv_ctr_rotate=[90,0,0])

        if ik_leg is True:
            # ---Will constraint the ik hdl to the ik control later(when creating ik foot),
            # so set the constraint_ik_ctr to false now.
            l_ik_leg_chain, l_ik_leg_ctrs_grp, l_ik_leg_ctr, l_ik_leg_hdl = self.create_ik_limb(root_jnt_key="l_thigh", mid_jnt_key="l_knee", end_jnt_key="l_ankle",
                                                                                                main_name="leg", constraint_ik_ctr=False, pv_ctr_rotate=[90,0,0])
            r_ik_leg_chain, r_ik_leg_ctrs_grp, r_ik_leg_ctr, r_ik_leg_hdl = self.create_ik_limb(root_jnt_key="r_thigh", mid_jnt_key="r_knee", end_jnt_key="r_ankle",
                                                                                                main_name="leg", constraint_ik_ctr=False, pv_ctr_rotate=[90,0,0])

            # Create ik feet:
            l_ik_foot_chain = self.create_ik_foot(ankle_jnt_key="l_ankle", ball_jnt_key="l_ball", toe_jnt_key="l_footTip",
                                                  leg_ik_ctr=l_ik_leg_ctr, leg_ik_hdl=l_ik_leg_hdl)[0]
            r_ik_foot_chain = self.create_ik_foot(ankle_jnt_key="r_ankle", ball_jnt_key="r_ball", toe_jnt_key="r_footTip",
                                                  leg_ik_ctr=r_ik_leg_ctr, leg_ik_hdl=r_ik_leg_hdl)[0]

            # Parent the ik feet to the ik leg end joints:
            l_ik_foot_chain[0] = mc.parent(l_ik_foot_chain[0], l_ik_leg_chain[-1])[0]
            r_ik_foot_chain[0] = mc.parent(r_ik_foot_chain[0], r_ik_leg_chain[-1])[0]

        # Create fk arms and legs:
        if fk_arm is True:
            l_fk_arm_chain, l_fk_arm_ctrs_grp = self.create_fk_limb(jnt_key_list=["l_shoulder", "l_elbow", "l_wrist"], main_name="arm")
            r_fk_arm_chain, r_fk_arm_ctrs_grp = self.create_fk_limb(jnt_key_list=["r_shoulder", "r_elbow", "r_wrist"], main_name="arm")

            # ---connect fk arm ctrs to clavicle ctr
            l_fk_arm_ctrs_grp = mc.parent(l_fk_arm_ctrs_grp, l_clavicle_ctr)[0]
            r_fk_arm_ctrs_grp = mc.parent(r_fk_arm_ctrs_grp, r_clavicle_ctr)[0]

        if fk_leg is True:
            l_fk_leg_chain, l_fk_leg_ctrs_grp = self.create_fk_limb(jnt_key_list=["l_thigh", "l_knee", "l_ankle", "l_ball"], main_name="leg")
            r_fk_leg_chain, r_fk_leg_ctrs_grp = self.create_fk_limb(jnt_key_list=["r_thigh", "r_knee", "r_ankle", "r_ball"], main_name="leg")

            # ---point constraint fk control grp to fk jnt
            mc.pointConstraint(l_fk_leg_chain[0], l_fk_leg_ctrs_grp)
            mc.pointConstraint(r_fk_leg_chain[0], r_fk_leg_ctrs_grp)

        # Create hands and foot controls, including fingers and toes
        l_hand_setting_space = self.create_digit_setting_ctrs(digit_root_jnt_list=self.get_anim_jnt_name(self.l_finger_root_jnt_key),
                                                              parent_jnt=self.get_anim_jnt_name("l_wrist"), rotate_digit_setting_ctr=[0, 90, 0],
                                                              move_digit_setting_ctr=[10, 7, 0], mid_name="handSetting")[0]
        r_hand_setting_space = self.create_digit_setting_ctrs(digit_root_jnt_list=self.get_anim_jnt_name(self.r_finger_root_jnt_key),
                                                              parent_jnt=self.get_anim_jnt_name("r_wrist"),rotate_digit_setting_ctr=[0, -90, 0],
                                                              move_digit_setting_ctr=[-10, -7, 0], mid_name="handSetting")[0]

        mc.parent(l_hand_setting_space, self.global_ctr)
        mc.parent(r_hand_setting_space, self.global_ctr)

        if toe_count > 0:
            l_foot_setting_space = self.create_digit_setting_ctrs(digit_root_jnt_list=self.get_anim_jnt_name(self.l_toe_root_jnt_key),
                                                                  parent_jnt=self.get_anim_jnt_name("l_ball"), rotate_digit_setting_ctr=[0, 90, 0],
                                                                  move_digit_setting_ctr=[10, -7, 0], mid_name="footSetting")[0]
            r_foot_setting_space = self.create_digit_setting_ctrs(digit_root_jnt_list=self.get_anim_jnt_name(self.r_toe_root_jnt_key),
                                                                  parent_jnt=self.get_anim_jnt_name("r_ball"), rotate_digit_setting_ctr=[0, -90, 0],
                                                                  move_digit_setting_ctr=[-10, 7, 0], mid_name="footSetting")[0]

            mc.parent(l_foot_setting_space, self.global_ctr)
            mc.parent(r_foot_setting_space, self.global_ctr)

        # Blend ik and fk limbs:
        # ----get the animate joint chains first
        l_arm_anim_jnt_chain = self.get_anim_jnt_name(["l_shoulder", "l_elbow", "l_wrist"])
        r_arm_anim_jnt_chain = self.get_anim_jnt_name(["r_shoulder", "r_elbow", "r_wrist"])
        l_leg_anim_jnt_chain = self.get_anim_jnt_name(["l_thigh", "l_knee", "l_ankle", "l_ball"])
        r_leg_anim_jnt_chain = self.get_anim_jnt_name(["r_thigh", "r_knee", "r_ankle", "r_ball"])

        # If no IK/FK arm/leg needed, assign the related jnt chains and control groups to none.
        if not ik_arm:
            l_ik_arm_chain, l_ik_arm_ctrs_grp, r_ik_arm_chain, r_ik_arm_ctrs_grp = [None], None, [None], None
        if not fk_arm:
            l_fk_arm_chain, l_fk_arm_ctrs_grp, r_fk_arm_chain, r_fk_arm_ctrs_grp = [None], None, [None], None
        if not ik_leg:
            l_ik_leg_chain, l_ik_foot_chain, l_ik_leg_ctrs_grp, r_ik_leg_chain, r_ik_foot_chain, r_ik_leg_ctrs_grp = [None], [None], None, [None], [None], None
        if not fk_leg:
            l_fk_leg_chain, l_fk_leg_ctrs_grp, r_fk_leg_chain, r_fk_leg_ctrs_grp = [None], None, [None], None

        self.blend_ik_fk_limb(ik_jnt_chain=l_ik_arm_chain, fk_jnt_chain=l_fk_arm_chain, anim_jnt_chain=l_arm_anim_jnt_chain,
                              blend_attr_name="lArmIkFk", blend_ctr=self.global_ctr, ik_ctrs_grp=l_ik_arm_ctrs_grp,
                              fk_ctrs_grp=l_fk_arm_ctrs_grp)
        self.blend_ik_fk_limb(ik_jnt_chain=r_ik_arm_chain, fk_jnt_chain=r_fk_arm_chain, anim_jnt_chain=r_arm_anim_jnt_chain,
                              blend_attr_name="rArmIkFk", blend_ctr=self.global_ctr, ik_ctrs_grp=r_ik_arm_ctrs_grp,
                              fk_ctrs_grp=r_fk_arm_ctrs_grp)
        self.blend_ik_fk_limb(ik_jnt_chain=l_ik_leg_chain[:-1]+l_ik_foot_chain[:-1], fk_jnt_chain=l_fk_leg_chain, anim_jnt_chain=l_leg_anim_jnt_chain,
                              blend_attr_name="lLegIkFk", blend_ctr=self.global_ctr, ik_ctrs_grp=l_ik_leg_ctrs_grp,
                              fk_ctrs_grp=l_fk_leg_ctrs_grp)
        self.blend_ik_fk_limb(ik_jnt_chain=r_ik_leg_chain[:-1]+r_ik_foot_chain[:-1], fk_jnt_chain=r_fk_leg_chain, anim_jnt_chain=r_leg_anim_jnt_chain,
                              blend_attr_name="rLegIkFk", blend_ctr=self.global_ctr, ik_ctrs_grp=r_ik_leg_ctrs_grp ,
                              fk_ctrs_grp=r_fk_leg_ctrs_grp)

        # Create Stretch arms and legs:
        stretch_loop_dict = {}
        if stretch_arm and ik_arm:
            stretch_loop_dict.update({"l_arm": [l_ik_arm_ctr, l_ik_arm_chain], "r_arm": [r_ik_arm_ctr, r_ik_arm_chain]})

        if stretch_leg and ik_leg:
            stretch_loop_dict.update({"l_leg": [l_ik_leg_ctr, l_ik_leg_chain], "r_leg": [r_ik_leg_ctr, r_ik_leg_chain]})

        for limb_name, ctr_and_chain_list in stretch_loop_dict.items():
            ik_arm_ctr = ctr_and_chain_list[0]
            ik_arm_chain = ctr_and_chain_list[1]
            self.create_stretch_limb(ik_ctr=ik_arm_ctr, end_jnt=ik_arm_chain[0],stretch_jnt_list=[ik_arm_chain[0], ik_arm_chain[1]],
                                     switch_ctr=self.global_ctr, limb_name=limb_name)

        self.connect_anim_and_bind()
        self.setup_global_scale()

        # Clean up stuff
        # --- disconnect the clavicle and neck joints from spine joints, in order to fix the scale issue
        for jnt_key in ["l_clavicle", "r_clavicle", "c_neck01"]:
            mc.parent(self.get_anim_jnt_name(jnt_key), self.anim_jnt_grp)

        # --- use point constraint to connect the neck to the spine
        mc.pointConstraint(self.get_anim_jnt_name(spine_jnt_key_list[-1]),
                           self.get_anim_jnt_name(neck_jnt_key_list[0]), maintainOffset=True)

        # --- hide attr from some controls
        hide_attr = ["scale", "visibility"]
        util.hide_attr(hip_ctr, attrs=hide_attr)
        util.hide_attr(self.cog_ctr, attrs=hide_attr)
        for cla_ctr in  [r_clavicle_ctr, l_clavicle_ctr]:
            util.hide_attr(cla_ctr, attrs=hide_attr)

        # hide misc and anim joint group
        mc.setAttr(self.anim_jnt_grp+".visibility", 0)
        mc.setAttr(self.bind_jnt_grp + ".visibility", 1)
        mc.setAttr(self.misc_grp + ".visibility", 0)

    def init_jnt_orientation(self, mirror_behavior=True):
        """
        Correct all the joints orientation, mainly make them aim to the right direction before creating other stuff.
        """
        # The first joint in the joint chain should aim to the second one,
        # the second one should aim to the third one, so far and so forth...
        center_jnt_chain_list = ["c_neck", "c_head", "c_headTip"]
        l_arm_chain_list = ["l_clavicle", "l_shoulder", "l_elbow", "l_wrist"]
        l_leg_chain_list = ["l_thigh", "l_knee"]
        l_foot_chain_list = ["l_ankle", "l_ball", "l_footTip"]
        r_arm_chain_list = ["r_clavicle", "r_shoulder", "r_elbow", "r_wrist"]
        r_leg_chain_list = ["r_thigh", "r_knee"]
        r_foot_chain_list = ["r_ankle", "r_ball", "r_footTip"]

        # Get all the digit(toes and fingers) joint chains and put them in a list
        all_digits_chain_list = []
        for digit_root_list in [self.l_finger_root_jnt_key, self.r_finger_root_jnt_key]:
            all_digits_chain_list.append(self.get_digit_jnt_chain(digit_root_list=digit_root_list, child_jnt_count=3))

        for digit_root_list in [self.l_toe_root_jnt_key, self.r_toe_root_jnt_key]:
            all_digits_chain_list.append(self.get_digit_jnt_chain(digit_root_list=digit_root_list, child_jnt_count=2))

        all_l_fingers_chain_list, all_r_fingers_chain_list, all_l_toes_chain_list, all_r_toes_chain_list = all_digits_chain_list

        # put all the joint chains that need to re-aim in a list
        jnt_chains_need_aimming = [center_jnt_chain_list, l_arm_chain_list, l_leg_chain_list+l_foot_chain_list, r_arm_chain_list, r_leg_chain_list+r_foot_chain_list]

        for digits_chain_list in all_digits_chain_list:
            for single_digit_chain in digits_chain_list:
                jnt_chains_need_aimming.append(single_digit_chain)

        for jnt_chain in jnt_chains_need_aimming:
            util.aim_jnt(self.get_bnd_jnt_name(jnt_chain))

        # Make wrist joint orientation to the same as elbow
        util.set_jnt_orient(self.get_bnd_jnt_name("l_wrist"), target_jnt=self.get_bnd_jnt_name("l_elbow"))
        util.set_jnt_orient(self.get_bnd_jnt_name("r_wrist"), target_jnt=self.get_bnd_jnt_name("r_elbow"))

        # Connect all the bind joints
        for jnt_key, jnt_info in self.bind_jnt_info_dict.items():
            if jnt_info["parent_uuid"] is not None:
                mc.parent(self.get_bnd_jnt_name(jnt_key), mc.ls(jnt_info["parent_uuid"])[0])

        # Sync joint orientation
        # --- reorient all the leg joints
        for jnt in self.get_bnd_jnt_name(l_leg_chain_list+r_leg_chain_list):
            mc.joint(jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="zdown")

        # --- reorient all the foot joints, need to unparent all the toes first,
        #     otherwise the ball joint will point to one of the toes.
        for toe_root_key in self.l_toe_root_jnt_key+self.r_toe_root_jnt_key:
            mc.parent(self.get_bnd_jnt_name(toe_root_key), self.rig_grp)

        for jnt in self.get_bnd_jnt_name(l_foot_chain_list[:-1]+r_foot_chain_list[:-1]):
            mc.joint(jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="ydown")

        for toe_chain in all_l_toes_chain_list + all_r_toes_chain_list:
            for toe_jnt in  self.get_bnd_jnt_name(toe_chain[:-1]):
                mc.joint(toe_jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="ydown")

        # --- parent back the toes to the ball joints
        for toe_root_key in self.l_toe_root_jnt_key+self.r_toe_root_jnt_key:
            mc.parent(self.get_bnd_jnt_name(toe_root_key), mc.ls(self.bind_jnt_info_dict[toe_root_key]["parent_uuid"]))

        # --- reorient all arm joints
        for jnt in self.get_bnd_jnt_name(l_arm_chain_list[:-1] + r_arm_chain_list[:-1]):
            mc.joint(jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="yup")

        # --- zero out footTip joints orientation to match their parent
        mc.makeIdentity(self.get_bnd_jnt_name("l_footTip"), rotate=True, jointOrient=True, apply=True)
        mc.makeIdentity(self.get_bnd_jnt_name("r_footTip"), rotate=True, jointOrient=True, apply=True)

        # --- reorient all the finger joints
        for i, finger_chain_list in enumerate((all_l_fingers_chain_list + all_r_fingers_chain_list)):
            for finger_jnt in self.get_bnd_jnt_name(finger_chain_list[:-1]):
                if "thumb" in finger_jnt:
                    mc.joint(finger_jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="zup")
                else:
                    mc.joint(finger_jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="yup")
            # zero out the end finger joints orientation to match their parent
            mc.makeIdentity(self.get_bnd_jnt_name(finger_chain_list[-1]), rotate=True, jointOrient=True, apply=True)

        # Change the joint orientation if mirror behavior mode is on
        if mirror_behavior is True:
            jnts_need_to_change = r_leg_chain_list + r_foot_chain_list + r_arm_chain_list
            for r_finger_chain in all_r_fingers_chain_list:
                jnts_need_to_change += r_finger_chain

            for r_toe_chain in all_r_toes_chain_list:
                jnts_need_to_change += r_toe_chain

            for jnt in self.get_bnd_jnt_name(jnts_need_to_change):
                util.set_jnt_orient(jnt, add_rot=[0, 0, 180])

    def create_pelvis_jnt(self):
        """
        Create pelvis joint, update the bind joint dictionary and manage the hierarchy
        """
        root_jnt = self.get_bnd_jnt_name("c_root")

        pelvis_jnt = mc.duplicate(root_jnt, parentOnly=True)[0]

        pelvis_jnt_key = CENTER_PREFIX + SEPARATOR + "pelvis"
        pelvis_jnt = mc.rename(pelvis_jnt, SEPARATOR.join([util.clear_path(self.rig_grp), pelvis_jnt_key, BIND_JNT_SUFFIX]))

        pelvis_jnt = mc.parent(pelvis_jnt, root_jnt)[0]
        mc.parent(self.get_bnd_jnt_name("l_thigh"), pelvis_jnt)
        mc.parent(self.get_bnd_jnt_name("r_thigh"), pelvis_jnt)

        # Update bind joint dictionary
        jnt_info = {}
        jnt_info["uuid"] = self.get_uuid(pelvis_jnt)
        self.bind_jnt_info_dict[pelvis_jnt_key] = jnt_info

    def create_general_spine(self, spine_root_jnt, spine_end_jnt, spine_jnt_count=5, jnt_mid_name="spine"):
        """
        Use to create a spine alike joint chain, like spine, neck, tail..etc, every joint has an equal position
        """
        spine_end_jnt = mc.parent(spine_end_jnt, spine_root_jnt)[0]
        spine_jnt_chain = [spine_root_jnt] + util.split_jnt_chain(spine_root_jnt, spine_jnt_count-1) + [spine_end_jnt]

        # Sync the joint orientation
        for jnt in spine_jnt_chain[:-1]:
            mc.joint(jnt, edit=True, orientJoint="xyz", secondaryAxisOrient="xdown")
        mc.makeIdentity(spine_end_jnt, rotate=True, jointOrient=True, apply=True)

        # rename all the joints and update the bind joint info dictionary
        spine_jnt_key_list = []
        for i, spine_jnt in enumerate(spine_jnt_chain):
            if i < len(spine_jnt_chain)-1:
                jnt_seq_no = str((i+1)).zfill(2)
            else:
                jnt_seq_no = "End"

            spine_jnt_key = CENTER_PREFIX + SEPARATOR + jnt_mid_name + jnt_seq_no
            spine_jnt_name = SEPARATOR.join([self.rig_grp.split(PATH_SLASH)[-1], spine_jnt_key, BIND_JNT_SUFFIX])
            spine_jnt_name = mc.rename(spine_jnt, spine_jnt_name)

            spine_jnt_info = {}
            spine_jnt_info["uuid"] = self.get_uuid(spine_jnt_name)

            spine_jnt_chain[i] = spine_jnt_name
            spine_jnt_key_list.append(spine_jnt_key)
            self.bind_jnt_info_dict[spine_jnt_key] = spine_jnt_info

        return spine_jnt_key_list

    def create_spine(self, spine_jnt_count=5):
        """
        Create spine joints based on the input joint count
        """
        spine_root_jnt = mc.duplicate(self.get_bnd_jnt_name("c_root"), parentOnly=True)[0]
        spine_end_jnt = mc.duplicate(self.get_bnd_jnt_name("c_neck"), parentOnly=True)[0]

        spine_jnt_key_list = self.create_general_spine(spine_root_jnt= spine_root_jnt, spine_end_jnt=spine_end_jnt,
                                                       spine_jnt_count=spine_jnt_count, jnt_mid_name="spine")

        return spine_jnt_key_list

    def create_neck(self, neck_jnt_count=3):
        """
        Create neck joints based on the input joint count
        """
        neck_root_jnt = mc.duplicate(self.get_bnd_jnt_name("c_neck"), parentOnly=True)[0]
        neck_end_jnt = mc.duplicate(self.get_bnd_jnt_name("c_head"), parentOnly=True)[0]

        neck_jnt_key_list = self.create_general_spine(spine_root_jnt=neck_root_jnt, spine_end_jnt=neck_end_jnt,
                                                      spine_jnt_count=neck_jnt_count, jnt_mid_name="neck")

        neck_jnt_chain = self.get_bnd_jnt_name(neck_jnt_key_list)

        # c_neck joint will be replaced by c_neck01, so delete it in here
        neck_root_jnt = neck_jnt_chain[-1]
        mc.parent(self.get_bnd_jnt_name("c_head"), neck_root_jnt)
        mc.delete(self.get_bnd_jnt_name("c_neck"))
        self.bind_jnt_info_dict.pop("c_neck")

        return neck_jnt_key_list

    def create_neck_ctr(self, neck_jnt_chain, ctr_scale=[10,10,10]):
        ctr_space_list, ctr_list = util.create_fk_ctrs(neck_jnt_chain, ctr_scale=ctr_scale)

        for i in range(len(ctr_space_list)):
            ctr_space_list[i] = mc.rename(ctr_space_list[i],
                                          util.change_suffix(util.clear_path(neck_jnt_chain[i]), SPACE_GRP_SUFFIX))
            ctr_list[i] = mc.rename(ctr_list[i],
                                    util.change_suffix(util.clear_path(neck_jnt_chain[i]), CONTROL_SUFFIX))

        return ctr_space_list, ctr_list

    def create_ribbon_spine(self, spine_jnt_chain):
        """
        Create ribbon spine system based on the input spine joint chain
        """
        chain_list_len = len(spine_jnt_chain)

        if chain_list_len % 2 == 0:
            return

        # Get the root, middle and end spine joint.
        mid_jnt = spine_jnt_chain[chain_list_len // 2]
        root_jnt = spine_jnt_chain[0]
        end_jnt = spine_jnt_chain[-1]

        root_pos = mc.xform(root_jnt, query=True, translation=True, worldSpace=True)
        end_pos = mc.xform(end_jnt, query=True, translation=True, worldSpace=True)

        # Create nurbs surface, move it to the center of the spine, scale it up to the length of the spine
        start_end_distance = util.get_distance(root_pos, end_pos)
        spine_surf = mc.nurbsPlane(u=2)[0]
        spine_surf_shape = mc.listRelatives(spine_surf)[0]

        cst = mc.parentConstraint(mid_jnt, spine_surf, maintainOffset=False)
        mc.delete(cst)

        util.rotate_cvs(spine_surf, y=-90)
        util.scale_cvs(spine_surf, x=start_end_distance)
        mc.makeIdentity(spine_surf, scale=True, apply=True)

        # Create clusters for controlling the spine
        prefix = util.clear_path(self.rig_grp)
        root_cluster = mc.cluster(spine_surf + ".cv[0:7]", name=SEPARATOR.join([prefix, CENTER_PREFIX, "spineRoot", CLUSTER_SUFFIX]))[1]
        mid_cluster = mc.cluster(spine_surf + ".cv[8:11]", name=SEPARATOR.join([prefix, CENTER_PREFIX, "spineMid", CLUSTER_SUFFIX]))[1]
        end_cluster = mc.cluster(spine_surf + ".cv[12:19]", name=SEPARATOR.join([prefix, CENTER_PREFIX, "spineEnd", CLUSTER_SUFFIX]))[1]

        # Create follicle nodes and connect them to the nurbs surface
        param_u_delta = 1.0/(chain_list_len-1)
        for i, spine_jnt in enumerate(spine_jnt_chain):
            fol_shape = mc.createNode('follicle')
            fol_node = mc.listRelatives(fol_shape, parent=True)[0]
            mc.setAttr(fol_shape+".parameterU", param_u_delta*i)
            mc.setAttr(fol_shape+".parameterV", 0.5)
            mc.connectAttr(spine_surf_shape + ".local", fol_shape + ".inputSurface")
            mc.connectAttr(spine_surf_shape + ".worldMatrix[0]", fol_shape + ".inputWorldMatrix")
            mc.connectAttr(fol_shape + ".outRotate", fol_node + ".rotate")
            mc.connectAttr(fol_shape + ".outTranslate", fol_node + ".translate")
            spine_jnt_key = self.get_jnt_key(util.clear_path(spine_jnt_chain[i]))
            spine_jnt_chain[i] = mc.parent(self.get_anim_jnt_name(spine_jnt_key), fol_node)[0]
            fol_node = mc.rename(fol_node, util.change_suffix(util.clear_path(spine_jnt), FOLLICLE_SUFFIX))
            mc.parent(fol_node, self.misc_grp)

        # Create controls
        mid_name_list = ["spineRoot", "spineMid", "spineEnd"]
        cluster_list = [root_cluster, mid_cluster, end_cluster]
        ctr_list, ctr_space_list, fk_ctr_space_list, fk_ctr_list = [], [], [], []
        for i in range(len(cluster_list)):
            cluster_list[i] = mc.parent(cluster_list[i], self.misc_grp)[0]

            ctr_space, ctr = util.create_ctr_cuv(pos=mc.xform(cluster_list[i], query=True, rotatePivot=True, worldSpace=True),
                                                 ctr_type="cube", scale_cv=[30, 5, 10],
                                                 ctr_name=SEPARATOR.join([prefix, CENTER_PREFIX, mid_name_list[i] + "Ik", CONTROL_SUFFIX]),
                                                 space_name=SEPARATOR.join([prefix, CENTER_PREFIX, mid_name_list[i] + "Ik", SPACE_GRP_SUFFIX]))
            fk_ctr_space, fk_ctr = util.create_ctr_cuv(match_obj=ctr, ctr_type="circle", rotate_cv=[0, 0 ,90], scale_cv=[25, 25, 25],
                                                       ctr_name=SEPARATOR.join([prefix, CENTER_PREFIX, mid_name_list[i] + "Fk", CONTROL_SUFFIX]),
                                                       space_name=SEPARATOR.join([prefix, CENTER_PREFIX, mid_name_list[i] + "Fk", SPACE_GRP_SUFFIX]))

            mc.parentConstraint(ctr, cluster_list[i], maintainOffset=True)
            mc.scaleConstraint(ctr, cluster_list[i], maintainOffset=True)
            util.hide_attr(ctr, attrs=["scale", "visibility"])
            util.hide_attr(fk_ctr, attrs=["translate", "scale", "visibility"])

            ctr_space = mc.parent(ctr_space,  fk_ctr)[0]

            if (i > 0):
                fk_ctr_space = mc.parent(fk_ctr_space, fk_ctr_list[i - 1])[0]

            ctr_list.append(ctr)
            ctr_space_list.append(ctr_space)
            fk_ctr_space_list.append(fk_ctr_space)
            fk_ctr_list.append(fk_ctr)

        spine_surf = mc.rename(spine_surf, SEPARATOR.join([prefix, CENTER_PREFIX, "spineSurf", NURBS_SURF_SUFFIX]))
        spine_surf = mc.parent(spine_surf, self.misc_grp)[0]

        fk_ctr_space_list[0] = mc.parent(fk_ctr_space_list[0], self.global_ctr)[0]

        return ctr_space_list, ctr_list, fk_ctr_space_list, fk_ctr_list

    def create_general_ctr(self, jnt=None, pos=[0,0,0],  cst_types=["parent"], ctr_type="circle", ctr_scale=[1,1,1], ctr_rot=[0,0,0], ctr_move=[0,0,0],
                           parent=None, mid_name=None, flip_ctr=False):
        """
        Create clavicle controls
        """
        if jnt is not None:
            pos = mc.xform(jnt, query=True, translation=True, worldSpace=True)
        ctr_space, ctr = util.create_ctr_cuv(pos=pos, ctr_type=ctr_type, scale_cv=ctr_scale, move_cv=ctr_move, rotate_cv=ctr_rot)

        util.hide_attr(ctr, attrs=["visibility"])

        if mid_name is None:
            mid_name = self.get_jnt_key(util.clear_path(jnt))
        prefix = util.clear_path(self.rig_grp)

        ctr_space = mc.rename(ctr_space, SEPARATOR.join([prefix, mid_name, SPACE_GRP_SUFFIX]))

        if flip_ctr is True:
            mc.scale(-1, 1, 1, ctr_space)

        if jnt is not None:
            for cst_type in cst_types:
                if cst_type == "parent":
                    mc.parentConstraint(ctr, jnt, maintainOffset=True)
                elif cst_type == "orient":
                    mc.orientConstraint(ctr, jnt, maintainOffset=True)

        if parent is None:
            parent = self.ctr_grp

        ctr_space = mc.parent(ctr_space, parent)[0]
        ctr = mc.rename(ctr, SEPARATOR.join([prefix, mid_name, CONTROL_SUFFIX]))

        return ctr_space, ctr

    def create_ik_limb(self, root_jnt_key, mid_jnt_key, end_jnt_key, main_name, constraint_ik_ctr=True, constraint_pv_ctr=True,
                       ik_ctr_rotate = [0,0,0], pv_ctr_rotate = [0,0,0], ik_ctr_scale= [10,10,10], pv_ctr_scale= [10,10,10],
                       match_jnt_orient=False):
        """
        Create IK limb, controls. Rename all new objects and put them in the right groups
        """
        ik_jnt_chain, ik_hdl, ik_ctr_space, ik_ctr, pv_ctr_space, pv_ctr = util.create_ik_limb(root_jnt=self.get_anim_jnt_name(root_jnt_key),
                                                                                               mid_jnt=self.get_anim_jnt_name(mid_jnt_key),
                                                                                               end_jnt=self.get_anim_jnt_name(end_jnt_key),
                                                                                               constraint_ik_ctr=constraint_ik_ctr,
                                                                                               constraint_pv_ctr=constraint_pv_ctr,
                                                                                               ik_ctr_rotate=ik_ctr_rotate,
                                                                                               pv_ctr_rotate=pv_ctr_rotate,
                                                                                               ik_ctr_scale=ik_ctr_scale,
                                                                                               pv_ctr_scale=pv_ctr_scale,
                                                                                               match_jnt_orient=match_jnt_orient
                                                                                               )
        # Get the animate names for renaming the new IK joints
        animate_jnt_chain = self.get_anim_jnt_name([root_jnt_key, mid_jnt_key, end_jnt_key])

        for i, ik_jnt in enumerate(ik_jnt_chain):
            ik_jnt_chain[i] = mc.rename(ik_jnt, util.change_suffix(util.clear_path(animate_jnt_chain[i]), IK_JNT_SUFFIX))

        prefix = util.clear_path(self.rig_grp)
        left_or_right = root_jnt_key.split(SEPARATOR)[0]

        ik_hdl = mc.rename(ik_hdl, SEPARATOR.join([prefix, left_or_right, main_name+"Ik", IK_HANDLE_SUFFIX]))
        ik_hdl = mc.parent(ik_hdl, self.misc_grp)[0]

        ik_ctr_space = mc.rename(ik_ctr_space, SEPARATOR.join([prefix, left_or_right, main_name+"Ik", SPACE_GRP_SUFFIX]))
        ik_ctr = mc.rename(ik_ctr, SEPARATOR.join([prefix, left_or_right,  main_name+"Ik", CONTROL_SUFFIX]))

        pv_ctr_space = mc.rename(pv_ctr_space, SEPARATOR.join([prefix, left_or_right, main_name+"Pv", SPACE_GRP_SUFFIX]))
        pv_ctr = mc.rename(pv_ctr, SEPARATOR.join([prefix, left_or_right,  main_name+"Pv", CONTROL_SUFFIX]))

        ik_ctrs_grp = mc.group(name=SEPARATOR.join([prefix, left_or_right, main_name + "IkCtrs", GRP_SUFFIX]),
                               parent=self.rig_grp, empty=True)

        ik_ctr_space = mc.parent(ik_ctr_space, ik_ctrs_grp)[0]
        pv_ctr_space = mc.parent(pv_ctr_space, ik_ctrs_grp)[0]
        ik_ctrs_grp = mc.parent(ik_ctrs_grp, self.global_ctr)[0]

        return ik_jnt_chain, ik_ctrs_grp, ik_ctr, ik_hdl

    def create_ik_foot(self, ankle_jnt_key, ball_jnt_key, toe_jnt_key, leg_ik_ctr, leg_ik_hdl):
        """
        Create IK foot and add foot roll attributes to foot control
        """

        ankle_jnt = self.get_anim_jnt_name(ankle_jnt_key)
        ball_jnt = self.get_anim_jnt_name(ball_jnt_key)
        toe_jnt = self.get_anim_jnt_name(toe_jnt_key)

        prefix = util.clear_path(self.rig_grp)
        left_or_right = ankle_jnt_key.split(SEPARATOR)[0]

        # Create ik joints
        ankle_drv_jnt = mc.duplicate(ankle_jnt, name=util.change_suffix(util.clear_path(ankle_jnt), DRIVER_SUFFIX), parentOnly=True)[0]
        ball_ik = mc.duplicate(ball_jnt, name=util.change_suffix(util.clear_path(ball_jnt), IK_JNT_SUFFIX), parentOnly=True)[0]
        toe_ik = mc.duplicate(toe_jnt, name=util.change_suffix(util.clear_path(toe_jnt), IK_JNT_SUFFIX), parentOnly=True)[0]

        toe_ik = mc.parent(toe_ik, ball_ik)[0]
        ball_ik = mc.parent(ball_ik, ankle_drv_jnt)[0]

        # Create locators for heel roll, ball roll, toe roll
        locs = []
        for name in ["toeRoll",  "ballRoll", "heelRoll", "ankleRoll"]:
            loc = mc.spaceLocator(name=SEPARATOR.join([prefix, left_or_right, name, LOCATOR_SUFFIX]))[0]
            locs.append(loc)
        toe_loc, ball_loc, heel_loc, ankle_loc = locs

        for loc, jnt in {toe_loc: toe_ik, ball_loc: ball_ik, ankle_loc: ankle_drv_jnt}.items():
            util.move_to_obj(original_obj=loc, target_obj=jnt, maintain_rot=False)

        # moe heel locator from ankle to the ground along the y axis
        util.move_to_obj(original_obj=heel_loc, target_obj=ankle_drv_jnt, maintain_rot=False)
        heel_loc_pos = mc.xform(ankle_drv_jnt, query=True, translation=True, worldSpace=True)
        mc.move(heel_loc_pos[0], 0, heel_loc_pos[2], heel_loc)

        # Managing the hierarchy, ball should parent to toe, toe parent to heel
        ball_grp, ball_loc = util.create_space_grp(ball_loc)
        toe_grp, toe_loc = util.create_space_grp(toe_loc)
        heel_grp, heel_loc = util.create_space_grp(heel_loc)
        ankle_grp, ankle_loc = util.create_space_grp(ankle_loc)

        ankle_grp = mc.parent(ankle_grp, ball_loc)[0]
        ball_grp = mc.parent(ball_grp, toe_loc)[0]
        toe_grp = mc.parent(toe_grp, heel_loc)[0]

        # create foot roll attributes and connect them to the nodes
        attrs = ["heelRoll", "ballRoll", "toeRoll", "toeLift"]
        for attr in attrs:
            mc.addAttr(leg_ik_ctr, longName=attr, attributeType='float', keyable=True)

        # Connect foot roll attrs to toe roatation z
        mc.connectAttr(leg_ik_ctr + ".toeRoll", toe_loc + ".rz")
        mc.connectAttr(leg_ik_ctr + ".ballRoll", ball_loc + ".rz")
        mc.connectAttr(leg_ik_ctr + ".heelRoll", heel_loc + ".rz")

        # Ball roll and toe left:
        pma_node = mc.createNode("plusMinusAverage")
        md_node = mc.createNode("multiplyDivide")
        mc.setAttr(md_node+".input2Z", -1)
        mc.connectAttr(leg_ik_ctr + ".ballRoll", pma_node + ".input1D[0]")
        mc.connectAttr(leg_ik_ctr + ".toeLift", pma_node + ".input1D[1]")
        mc.connectAttr(pma_node + ".output1D", md_node + ".input1Z")
        mc.connectAttr(md_node + ".outputZ", ball_ik + ".rz")

        mc.orientConstraint(ball_loc, ankle_drv_jnt, maintainOffset=True)
        mc.pointConstraint(ankle_loc, leg_ik_hdl, maintainOffset=True)

        mc.parent(heel_grp, leg_ik_ctr)

        return [ankle_drv_jnt, ball_ik, toe_ik], [heel_grp, toe_grp, ball_grp]

    def create_fk_limb(self, jnt_key_list, main_name):
        """
        Create FK limb, controls. Rename all new objects and put them in the right groups
        """
        # Use the original animate joint chain to create FK joint chain
        animate_jnt_chain = self.get_anim_jnt_name(jnt_key_list)
        fk_jnt_chain, fk_ctr_space_list, fk_ctr_list = util.create_fk_limb(animate_jnt_chain)

        for i, fk_jnt in enumerate(fk_jnt_chain):
            fk_jnt_chain[i] = mc.rename(fk_jnt,
                                        util.change_suffix(util.clear_path(animate_jnt_chain[i]), FK_JNT_SUFFIX))
            fk_ctr_list[i] = mc.rename(fk_ctr_list[i],
                                       util.change_suffix(util.clear_path(animate_jnt_chain[i]), CONTROL_SUFFIX))
            fk_ctr_space_list[i] = mc.rename(fk_ctr_space_list[i],
                                             util.change_suffix(util.clear_path(animate_jnt_chain[i]), SPACE_GRP_SUFFIX))

        prefix = util.clear_path(self.rig_grp)
        left_or_right = fk_jnt_chain[0].split(SEPARATOR)[1]
        fk_ctrs_grp = mc.group(name=SEPARATOR.join([prefix, left_or_right, main_name + "FkCtrs", GRP_SUFFIX]), empty=True, parent=self.ctr_grp)
        util.move_to_obj(fk_ctrs_grp, target_obj=fk_ctr_space_list[0])
        fk_ctr_space_list[0] =  mc.parent(fk_ctr_space_list[0], fk_ctrs_grp)[0]
        fk_ctrs_grp = mc.parent(fk_ctrs_grp, self.global_ctr)[0]

        return fk_jnt_chain, fk_ctrs_grp

    def blend_ik_fk_limb(self, ik_jnt_chain, fk_jnt_chain, anim_jnt_chain, blend_ctr, blend_attr_name,
                         ik_ctrs_grp, fk_ctrs_grp):
        """
        Blend the input IK FK chain to the animate chain, and add the control attribute to the input blend control
        """
        # Create blend colors node and add blend attribute on it
        only_fk = False
        only_ik = False

        if ik_ctrs_grp is None:
            only_fk = True
        if fk_ctrs_grp is None:
            only_ik = True

        if not (only_fk or only_ik):
            mc.addAttr(blend_ctr, longName=blend_attr_name, keyable=True, attributeType='float', minValue=0, maxValue=1)
            reverse_node = mc.createNode("reverse", name=util.change_suffix(util.clear_path(ik_ctrs_grp), REVERSE_NODE_SUFFIX))
            mc.connectAttr(blend_ctr+"."+blend_attr_name, reverse_node+".inputX")
            mc.connectAttr(reverse_node + ".outputX", ik_ctrs_grp+".visibility")
            mc.connectAttr(blend_ctr + "." + blend_attr_name, fk_ctrs_grp + ".visibility")

            # Connect fk, ik joints to animate joints
            for i in range((len(ik_jnt_chain))):
                ik_jnt = ik_jnt_chain[i]
                fk_jnt = fk_jnt_chain[i]
                anim_jnt = anim_jnt_chain[i]

                for attr in ["rotate", "scale"]:
                    bc_node = mc.createNode("blendColors", name=SEPARATOR.join([util.clear_path(self.rig_grp),
                                                                                self.get_jnt_key(ik_jnt)+attr, BLEND_COLORS_SUFFIX]))
                    mc.connectAttr(fk_jnt+"."+attr, bc_node+".color1")
                    mc.connectAttr(ik_jnt+"."+attr, bc_node+".color2")
                    mc.connectAttr(bc_node + ".output", anim_jnt + "." + attr)
                    mc.connectAttr(blend_ctr + "." + blend_attr_name, bc_node + ".blender")
        else:
            if only_fk:
                blend_jnt_chain = fk_jnt_chain
            else:
                blend_jnt_chain = ik_jnt_chain

            for i in range((len(blend_jnt_chain))):
                blend_jnt = blend_jnt_chain[i]
                anim_jnt = anim_jnt_chain[i]

                for attr in ["rotate", "scale"]:
                    bc_node = mc.createNode("blendColors", name=SEPARATOR.join([util.clear_path(self.rig_grp),
                                                                                self.get_jnt_key(blend_jnt) + attr,
                                                                                BLEND_COLORS_SUFFIX]))
                    mc.setAttr(bc_node+".blender", 1)
                    mc.connectAttr(blend_jnt + "." + attr, bc_node + ".color1")
                    mc.connectAttr(bc_node + ".output", anim_jnt + "." + attr)

    def create_digit_setting_ctrs(self, digit_root_jnt_list, parent_jnt, rotate_digit_setting_ctr=[0,90,0],
                                  move_digit_setting_ctr=[10,7,0], mid_name="digitSetting"):
        """
        Create digit(finger or toe) controls and their global control(hand and foot)
        """
        digit_setting_ctr_space, digit_setting_ctr = util.create_ctr_cuv(match_obj=parent_jnt, ctr_type="handSetting",
                                                                       scale_cv=[4,4,4], rotate_cv=rotate_digit_setting_ctr,
                                                                       move_cv=move_digit_setting_ctr)

        prefix = util.clear_path(self.rig_grp)
        l_or_r = (util.clear_path(parent_jnt)).split(SEPARATOR)[1]

        mc.parentConstraint(parent_jnt, digit_setting_ctr, maintainOffset=True)
        digit_setting_ctr_space = mc.parent(digit_setting_ctr_space, self.ctr_grp)
        digit_setting_ctr = mc.rename(digit_setting_ctr, SEPARATOR.join([prefix, l_or_r, mid_name, CONTROL_SUFFIX]))

        util.hide_attr(digit_setting_ctr)

        for digit_root_jnt in digit_root_jnt_list:
            digit_ctr_space_list = self.create_digit_ctrs(digit_root_jnt, digit_setting_ctr)[0]

        digit_setting_ctr_space =mc.rename(digit_setting_ctr_space,
                                          util.change_suffix(util.clear_path(digit_setting_ctr), SPACE_GRP_SUFFIX))

        return digit_setting_ctr_space, digit_setting_ctr

    def create_digit_ctrs(self, digit_root_jnt, digit_setting_ctr):
        """
        Create digit(finger or toe) control
        """
        digit_jnt_chain = [digit_root_jnt] + mc.listRelatives(digit_root_jnt, allDescendents=True, type="joint",
                                                                noIntermediate=True, fullPath=True)[::-1][:-1]
        digit_ctr_space_list, digit_ctr_list, digit_ctr_offset_list = util.create_fk_ctrs(digit_jnt_chain, ctr_scale=[3,3,3], add_offset=True)

        digit_name = self.get_jnt_key(digit_root_jnt)[:-2]
        curl_attr_name = digit_name+"Curl"
        mc.addAttr(digit_setting_ctr, longName=curl_attr_name, attributeType="float", keyable=True)

        for i in range(len(digit_jnt_chain)):
            digit_jnt_name = util.clear_path(digit_jnt_chain[i])
            digit_ctr_list[i] = mc.rename(digit_ctr_list[i], util.change_suffix(digit_jnt_name, CONTROL_SUFFIX))
            digit_ctr_offset_list[i] = mc.rename(digit_ctr_offset_list[i], util.change_suffix(digit_jnt_name, OFFSET_GRP_SUFFIX))
            digit_ctr_space_list[i] = mc.rename(digit_ctr_space_list[i], util.change_suffix(digit_jnt_name, SPACE_GRP_SUFFIX ))

            mc.connectAttr(digit_setting_ctr+"." + curl_attr_name,
                           util.clear_path(digit_ctr_offset_list[i]) + ".rotateZ")

        mc.parent(digit_ctr_space_list[0], digit_setting_ctr)
        return digit_ctr_space_list, digit_ctr_list, digit_ctr_offset_list

    def get_extra_digit(self, digit_count, left_or_right, name="extraFinger"):
        alphabet_list = string.ascii_uppercase
        extra_digit_root_list = []
        for i in range(digit_count):
            extra_root_key = left_or_right + SEPARATOR + name + alphabet_list[i] + "01"
            extra_digit_root_list.append(extra_root_key)

        return extra_digit_root_list

    def get_digit_jnt_chain(self, digit_root_list, child_jnt_count=3):
        all_digits_chain_list = []
        for digit_root in digit_root_list:
            digit_chain_list = []
            digit_chain_list.append(digit_root)
            for i in range(child_jnt_count):
                digit_chain_list.append(digit_root.replace("01", str(i+2).zfill(2)))

            all_digits_chain_list.append(digit_chain_list)

        return all_digits_chain_list

    def create_anim_skeleton(self):
        """
        Create animate joints based on the bind joints and return the animate joitns dictionary.
        function should be called before creating twist joint.
        """
        anim_root_jnt = mc.duplicate(self.get_bnd_jnt_name("c_root"))[0]

        child_anim_jnt_list = []

        for jnt_list in [anim_root_jnt], child_anim_jnt_list:
            for anim_jnt in jnt_list:
                anim_jnt = mc.rename(anim_jnt, util.change_suffix(util.clear_path(anim_jnt), ANIM_JNT_SUFFIX))
                jnt_key = self.get_jnt_key(anim_jnt)

                anim_jnt_info = {}
                anim_jnt_info["uuid"] = self.get_uuid(anim_jnt)
                self.anim_jnt_info_dict[jnt_key] = anim_jnt_info

            child_anim_jnt_list += mc.listRelatives(self.get_anim_jnt_name("c_root"),
                                                   allDescendents=True, type="joint", noIntermediate=True, fullPath=True)

    def connect_anim_and_bind(self):
        """
        Constraint the anim joints to bind joints
        """
        for jnt_key, jnt_info in self.bind_jnt_info_dict.items():
            bind_jnt = self.get_bnd_jnt_name(jnt_key)
            anim_jnt = self.get_anim_jnt_name(jnt_key)
            mc.parentConstraint(anim_jnt, bind_jnt, maintainOffset=False)
            mc.connectAttr(anim_jnt + ".scale", bind_jnt + ".scale")

    def setup_global_scale(self):
        """
        Add the essential scale constraint for global scaling
        """
        mc.scaleConstraint(self.global_ctr, self.anim_jnt_grp)
        mc.scaleConstraint(self.global_ctr, self.bind_jnt_grp)

    def create_twist_jnts(self, start_jnt, end_jnt, twist_rate_list=[-1, -0.5, -0.2], twist_axis="x", parent_to_end_jnt=False):
        """
        Create twist joints between two specific joints, twist joints will be driven by the first joint. The twist joint count
        depends on how many twist rate items in the twist_rate_list. For instance [-1, -0.5, -0.2], the first twist joint
        will not twist when the
        driver joint twist, the second will rotate 50% and the third will rotate 80%
        """
        twist_jnt_count = len(twist_rate_list)
        start_jnt_key = self.get_jnt_key(start_jnt)
        name_prefix = util.clear_path(self.rig_grp)

        # Create twist root jnt and end jnt, the end joint will be deleted latter
        twist_root_jnt = mc.duplicate(start_jnt, name=SEPARATOR.join([name_prefix, start_jnt_key+"Twist01", BIND_JNT_SUFFIX]),
                                      parentOnly=True)[0]
        twist_root_jnt = mc.parent(twist_root_jnt, self.rig_grp)[0]
        twist_end_jnt = mc.duplicate(end_jnt,  parentOnly=True)[0]
        twist_end_jnt = mc.parent(twist_end_jnt, self.rig_grp)[0]

        if parent_to_end_jnt is True:
            twist_root_jnt = util.set_jnt_orient(twist_root_jnt, target_jnt=twist_end_jnt)

        twist_end_jnt = mc.parent(twist_end_jnt, twist_root_jnt)[0]
        mc.makeIdentity(twist_end_jnt, rotate=True, jointOrient=True)

        # twist_jnt_list is used for holding all the new created twist joint name
        twist_jnt_list = [twist_root_jnt]

        # Create twist joints between the twist root and end,
        # if only has one twist joint, no need to create other in between twist joints
        if twist_jnt_count > 1:
            in_btw_twist_jnt_list = util.split_jnt_chain(twist_root_jnt, span_count=twist_jnt_count)

            for i, in_btw_jnt in enumerate(in_btw_twist_jnt_list):
                twist_jnt_name = mc.rename(in_btw_jnt, SEPARATOR.join([name_prefix, start_jnt_key+"Twist"+str(i+2).zfill(2), BIND_JNT_SUFFIX]))
                twist_jnt_name = mc.parent(twist_jnt_name, self.rig_grp)[0]
                twist_jnt_list.append(twist_jnt_name)

        mc.delete(twist_end_jnt)

        # Connect twist joints to their parent
        for i, twist_jnt in enumerate(twist_jnt_list):
            md_node = mc.createNode("multiplyDivide")
            mc.setAttr(md_node+".input2X", twist_rate_list[i])
            mc.connectAttr(start_jnt+".rotate"+twist_axis.upper(), md_node+".input1X")
            mc.connectAttr(md_node + ".outputX",  twist_jnt + ".rotateX")
            mc.rename(md_node, util.change_suffix(util.clear_path(twist_jnt), NODE_OBJ_SUFFIX))

            if not parent_to_end_jnt:
                parent_jnt = start_jnt
            else:
                parent_jnt = end_jnt

            try:
                twist_jnt_list[i] = mc.parent(twist_jnt, parent_jnt)[0]
            except RuntimeError:
                pass

            # twist joint orientation should follow the parent joint
            mc.joint(twist_jnt_list[i], edit=True, orientation=[0, 0, 0])

    def create_stretch_limb(self, ik_ctr, end_jnt, stretch_jnt_list, switch_ctr, limb_name, global_ctr=None):
        """
        Create stretch limb, rename the new created nodes and group
        """
        distance_dimen, start_loc, end_loc = util.create_stretch_limb(ik_ctr=ik_ctr, end_jnt=end_jnt, stretch_jnt_list=stretch_jnt_list,
                                                                      switch_ctr=switch_ctr, switch_attr_name=limb_name+"Stretch",
                                                                      global_ctr=self.global_ctr)

        prefix = util.clear_path(self.rig_grp)
        distance_dimen = mc.rename(distance_dimen, SEPARATOR.join([prefix, limb_name, DISTANCE_DIMEN_SUFFIX]))
        start_loc = mc.rename(start_loc, SEPARATOR.join([prefix, limb_name+"StretchStart", LOCATOR_SUFFIX]))
        end_loc = mc.rename(end_loc, SEPARATOR.join([prefix, limb_name + "StretchEnd", LOCATOR_SUFFIX]))

        stretch_grp = mc.group(distance_dimen, start_loc, end_loc, parent=self.misc_grp)
        stretch_grp = mc.rename(stretch_grp, SEPARATOR.join([prefix, limb_name+"Stretch", GRP_SUFFIX]))

        return stretch_grp

    def get_default_twist_rate(self, twist_jnt_count, counter_twist=True):
        """
        Calculate the default twist rate based on the twist joint count
        """
        delta = 1.0/twist_jnt_count
        twist_rate_list = []

        for i in range(twist_jnt_count):
            twist_rate = 1-i*delta
            if counter_twist is True:
                twist_rate *= -1
            twist_rate_list.append(twist_rate)

        return twist_rate_list

    def get_jnt_key(self, jnt_name):
        """
        Get the joint key by joint name, this only work for the name stick with the naming convention
        """
        try:
            jnt_name = util.clear_path(jnt_name)
            return SEPARATOR.join([jnt_name.split(SEPARATOR)[-3], jnt_name.split(SEPARATOR)[-2]])
        except IndexError:
            return ""

    def get_bnd_jnt_name(self, jnt_key):
        """
        Get the bind joint name by the joint key
        """
        return self.get_jnt_name(jnt_key, isBind=True)

    def get_anim_jnt_name(self, jnt_key):
        """
        Get the animate joint name by the joint key
        """
        return self.get_jnt_name(jnt_key, isAnim=True)

    def get_jnt_name(self, jnt_key, isBind=False, isAnim=False):
        """
        A common function to get the joint name, switch to different dictionary based on the input value.
        """
        if isBind:
            search_dict = self.bind_jnt_info_dict
        elif isAnim:
            search_dict = self.anim_jnt_info_dict

        if type(jnt_key) is not list:
            return mc.ls(search_dict[jnt_key]["uuid"])[0]
        else:
            result_list = []
            for k in jnt_key:
                result_list.append(mc.ls(search_dict[k]["uuid"])[0])
            return result_list

    def get_uuid(self, obj_name):
        """
        Get the object uuid by the object name
        """
        uuid = mc.ls(obj_name, uuid=True)[0]
        return uuid







