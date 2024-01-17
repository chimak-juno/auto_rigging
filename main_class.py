import maya.cmds as mc
from maya import OpenMayaUI as omui

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from shiboken import wrapInstance

import joint_placement_helper
reload(joint_placement_helper)
import auto_rigger
reload(auto_rigger)
import utility as util
reload(util)

# Widget Size
WIN_WIDTH = 300
WIN_HEIGHT = 800

# Label text
WIN_TITLE = "Auto Rigger"
BIPED_TYPE_LBL = "Biped"
QUADRU_TYPE_LBL = "Quadruped"
OTHER_TYPE_LBL = "Others"
BIPED_TYPE_LBL = "Biped"
TYPE_TITLE_LBL = "Type"
STRETCH_ARM_LBL = "Stretch Arms"
STRETCH_LEG_LBL = "Stretch Legs"
FK_IK_LBL = "FK and IK Setting"
STRETCH_LBL = "Sretch Setting"
FK_LEG_LBL = "FK Legs"
FK_ARM_LBL = "FK Arms"
IK_ARM_LBL = "IK Arms"
IK_LEG_LBL = "IK Legs"
SPINE_JNT_LBL = "Spine Joints:"
NECK_JNT_LBL = "Neck Joints:"
FINGER_CNT_LBL = "Fingers:"
TOE_CNT_LBL = "Toes:"
LOWER_ARM_TWIST_LBL = "Lower Arm Twist:"
UPPER_ARM_TWIST_LBL = "Upper Arm Twist:"
UPPER_LEG_TWIST_LBL = "Upper Leg Twist:"
LOWER_LEG_TWIST_LBL = "Lower Leg Twist:"
JNT_PLACEMENT_BTN_LBL = "Joint Placement"
CREATE_RIG_BTN_LBL = "Create Rig"
MIRROR_BEHV_LBL = "Mirror Behavior:"
SYMMETRY_LBL = "Symmetrical Character:"

# Default value
DEF_SPINE_JNT_CNT = 5
DEF_SPINE_JNT_RANGE = [3, 31]
DEF_NECK_JNT_CNT = 3
DEF_NECK_JNT_RANGE = [3, 31]
DEF_FINGER_CNT = 5
DEF_FINGER_CNT_RANGE = [1, 30]
DEF_TOE_CNT = 0
DEF_TOE_CNT_RANGE = [0, 26]
DEF_TWIST_JNT_CNT = 3
DEF_TWIST_JNT_RANGE = [0, 30]

# Warning Msg
NO_CHAR_NAME_ERR = "Please input character name."
SPINE_JNT_CNT_ODD_ERR = "Spine joints count should be an odd number."
TEMP_SKELETON_ERR = "Some problems were found in the template skeleton, please generate a new one."
CREATE_RIG_SUCCESS = "Rig has been created successfully!"
IK_FK_LEG_ERR = "Please select at least one IK/FK legs option."
IK_FK_ARM_ERR = "Please select at least one IK/FK arms option."

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)

class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        """
        Init all inputs, set inputs default value or label here
        """
        super(MainWindow,self).__init__(*args, **kwargs)
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.setMinimumSize(WIN_WIDTH, WIN_HEIGHT)

        # Define rigger instance
        self.auto_rigger = None
        self.jnt_placement_helper = None

        # Init instance variables
        self.char_name_line_edit = QLineEdit()  # Character Name

        self.biped_rdo_btn = QRadioButton(BIPED_TYPE_LBL)  # Rig type radio button
        self.quadru_rdo_btn = QRadioButton(QUADRU_TYPE_LBL)  # Rig type radio button
        self.other_rdo_btn = QRadioButton(OTHER_TYPE_LBL)  # Rig type radio button

        self.mirror_behv_chk_box = QCheckBox()  # Mirror behavior check box
        self.symmetry_chk_box = QCheckBox()  # Mirror behavior check box

        self.fk_arm_chk_box = QCheckBox(FK_ARM_LBL)  # fk arm check box
        self.fk_leg_chk_box = QCheckBox(FK_LEG_LBL)  # fk leg check box

        self.ik_arm_chk_box = QCheckBox(IK_ARM_LBL)  # ik arm check box
        self.ik_leg_chk_box = QCheckBox(IK_LEG_LBL)  # ik leg check box

        self.strh_arm_chk_box = QCheckBox(STRETCH_ARM_LBL)  # Stretch arm check box
        self.strh_leg_chk_box = QCheckBox(STRETCH_LEG_LBL)  # Stretch leg check box

        self.spine_jnts_spin = QSpinBox()  # Spine joints count spine box
        self.spine_jnts_spin.setValue(DEF_SPINE_JNT_CNT)
        self.spine_jnts_spin.setRange(DEF_SPINE_JNT_RANGE[0], DEF_SPINE_JNT_RANGE[1])

        self.spine_jnts_val_before_changed = DEF_SPINE_JNT_CNT

        self.neck_jnts_spin = QSpinBox()  # Neck joints count spine box
        self.neck_jnts_spin.setValue(DEF_NECK_JNT_CNT)
        self.neck_jnts_spin.setRange(DEF_NECK_JNT_RANGE[0], DEF_NECK_JNT_RANGE[1])
        
        self.finger_cnt_spin = QSpinBox()  # Fingers count spine box
        self.finger_cnt_spin.setValue(DEF_FINGER_CNT)
        self.finger_cnt_spin.setRange(DEF_FINGER_CNT_RANGE[0], DEF_FINGER_CNT_RANGE[1])

        self.toe_cnt_spin = QSpinBox()  # Toes count spine box
        self.toe_cnt_spin.setValue(DEF_TOE_CNT)
        self.toe_cnt_spin.setRange(DEF_TOE_CNT_RANGE[0], DEF_TOE_CNT_RANGE[1])

        # Twist joints count spine box
        self.upper_arm_twist_spin = QSpinBox()
        self.upper_leg_twist_spin = QSpinBox()
        self.lower_arm_twist_spin = QSpinBox()
        self.lower_leg_twist_spin = QSpinBox()

        self.jnt_placement_btn = QPushButton(JNT_PLACEMENT_BTN_LBL)  # Joint placement button
        self.create_rig_btn = QPushButton(CREATE_RIG_BTN_LBL)  # Create rig button

        # Put all user input boxes in a list
        self.jp_input_list = [self.char_name_line_edit, self.biped_rdo_btn, self.quadru_rdo_btn, self.other_rdo_btn,
                              self.spine_jnts_spin, self.neck_jnts_spin, self.finger_cnt_spin, self.toe_cnt_spin, self.upper_arm_twist_spin,
                              self.upper_leg_twist_spin, self.lower_arm_twist_spin, self.lower_leg_twist_spin, self.mirror_behv_chk_box, self.symmetry_chk_box]

        self.cg_input_list = [self.strh_arm_chk_box, self.strh_leg_chk_box,
                              self.fk_leg_chk_box, self.ik_leg_chk_box,
                              self.ik_arm_chk_box, self.fk_arm_chk_box]

        for input in self.cg_input_list:
            input.setEnabled(False)

    def init_ui(self):
        main_layout = QFormLayout(self)

        # Rig type radio buttons
        self.biped_rdo_btn.setChecked(True)
        self.quadru_rdo_btn.setEnabled(False)
        self.other_rdo_btn.setEnabled(False)
        type_rdo_grp_box = self.create_rdo_grp_box(rdo_btn_list=[self.biped_rdo_btn, self.quadru_rdo_btn, self.other_rdo_btn],
                                                   title=TYPE_TITLE_LBL)

        self.mirror_behv_chk_box.setChecked(True)
        self.symmetry_chk_box.setChecked(True)

        # Stretch arm and leg check box group
        self.strh_arm_chk_box.setChecked(True)
        self.strh_leg_chk_box.setChecked(True)
        strh_chk_grp_widget = self.create_chk_box_grp(chk_box_list=[self.strh_arm_chk_box, self.strh_leg_chk_box], title=STRETCH_LBL)

        self.spine_jnts_spin.valueChanged.connect(self.spine_count_val_changed)

        # FK arm and leg check box group
        self.fk_arm_chk_box.setChecked(True)
        self.fk_leg_chk_box.setChecked(True)
        self.ik_arm_chk_box.setChecked(True)
        self.ik_leg_chk_box.setChecked(True)
        fk_ik_chk_box_grp = self.create_chk_box_grp(chk_box_list=[self.fk_arm_chk_box, self.fk_leg_chk_box,
                                                                  self.ik_arm_chk_box, self.ik_leg_chk_box], title=FK_IK_LBL)

        self.ik_arm_chk_box.clicked.connect(lambda: self.ik_box_on_click(check_value=self.ik_arm_chk_box.isChecked(),
                                                                         connect_box=self.strh_arm_chk_box))
        self.ik_leg_chk_box.clicked.connect(lambda: self.ik_box_on_click(check_value=self.ik_leg_chk_box.isChecked(),
                                                                         connect_box=self.strh_leg_chk_box))

        # Twist joint count text box
        for spin in [self.upper_arm_twist_spin, self.upper_leg_twist_spin,
                     self.lower_arm_twist_spin, self.lower_leg_twist_spin]:
            spin.setValue(DEF_TWIST_JNT_CNT)
            spin.setRange(DEF_TWIST_JNT_RANGE[0], DEF_TWIST_JNT_RANGE[1])

        # Joint placement buttons
        self.jnt_placement_btn.clicked.connect(self.jnt_placement_btn_on_click)
        self.create_rig_btn.clicked.connect(self.create_rig_btn_on_click)
        self.create_rig_btn.setEnabled(False)

        # Add all inputs to the form layout
        main_layout.addRow(self.tr("&Character Name:"), self.char_name_line_edit)
        main_layout.addRow(type_rdo_grp_box)
        main_layout.addRow(self.tr(SYMMETRY_LBL), self.symmetry_chk_box)
        main_layout.addRow(self.tr(MIRROR_BEHV_LBL), self.mirror_behv_chk_box)
        main_layout.addRow(self.tr(SPINE_JNT_LBL), self.spine_jnts_spin)
        main_layout.addRow(self.tr(NECK_JNT_LBL), self.neck_jnts_spin)
        main_layout.addRow(self.tr(FINGER_CNT_LBL), self.finger_cnt_spin)
        main_layout.addRow(self.tr(TOE_CNT_LBL), self.toe_cnt_spin)
        main_layout.addRow(self.tr(UPPER_ARM_TWIST_LBL), self.upper_arm_twist_spin)
        main_layout.addRow(self.tr(LOWER_ARM_TWIST_LBL), self.lower_arm_twist_spin)
        main_layout.addRow(self.tr(UPPER_LEG_TWIST_LBL), self.upper_leg_twist_spin)
        main_layout.addRow(self.tr(LOWER_LEG_TWIST_LBL), self.lower_leg_twist_spin)
        main_layout.addRow(fk_ik_chk_box_grp)
        main_layout.addRow(strh_chk_grp_widget)
        main_layout.addRow(self.jnt_placement_btn)
        main_layout.addRow(self.create_rig_btn)

        self.setLayout(main_layout)
        self.setWindowTitle(WIN_TITLE)
        self.show()

    def jnt_placement_btn_on_click(self):
        """
        Joint placement button on click function. First validate the user input values, if all data correct than create a temp skeleton.
        """
        if not self.validate_input():
            return

        character_name = self.char_name_line_edit.text()

        # Crate temp skeleton
        self.jnt_placement_helper = joint_placement_helper.JointPlacementHelper()
        self.jnt_placement_helper.create_temp_skeleton(character_name=character_name, finger_count=self.finger_cnt_spin.value(),
                                                       toe_count=self.toe_cnt_spin.value(), symmetry=self.symmetry_chk_box.isChecked())
        self.char_name_line_edit.setText(util.clear_path(self.jnt_placement_helper.temp_grp))

        # Disable all inputs, enable create rig button
        for input in self.jp_input_list:
            input.setEnabled(False)
        for input in self.cg_input_list:
            input.setEnabled(True)
        self.jnt_placement_btn.setEnabled(False)
        self.create_rig_btn.setEnabled(True)

    def create_rig_btn_on_click(self):
        """
        Create rig button on click function.
        """
        self.create_rig_btn.setEnabled(False)
        for input in self.cg_input_list:
            input.setEnabled(False)
        try:
            rig_grp, bind_jnt_info_dict = self.jnt_placement_helper.finish_jnt_placement()
        except:
            # If the temp skeleton is broken or missing than send a warning message
            mc.warning(TEMP_SKELETON_ERR)
            return

        self.auto_rigger = auto_rigger.AutoRigger(rig_grp=rig_grp, bind_jnt_info_dict=bind_jnt_info_dict)
        self.auto_rigger.create_rig(spine_jnt_count=self.spine_jnts_spin.value(), neck_jnt_count=self.neck_jnts_spin.value(),
                                    upper_arm_twist_count=self.upper_arm_twist_spin.value(), lower_arm_twist_count=self.lower_arm_twist_spin.value(),
                                    upper_leg_twist_count=self.upper_leg_twist_spin.value(), lower_leg_twist_count=self.lower_leg_twist_spin.value(),
                                    mirror_behavior=self.mirror_behv_chk_box.isChecked(),
                                    ik_arm=self.ik_arm_chk_box.isChecked(), fk_arm=self.fk_arm_chk_box.isChecked(),
                                    ik_leg=self.ik_arm_chk_box.isChecked(), fk_leg=self.fk_leg_chk_box.isChecked(),
                                    stretch_arm=self.strh_arm_chk_box.isChecked(), stretch_leg=self.strh_leg_chk_box.isChecked(),
                                    finger_count=self.finger_cnt_spin.value(), toe_count=self.toe_cnt_spin.value())
        mc.warning(CREATE_RIG_SUCCESS)

    def validate_input(self):
        """
        Validate user input data.
        """
        if self.char_name_line_edit.text() == "":
            mc.warning(NO_CHAR_NAME_ERR)
            return False

        if (self.spine_jnts_spin.value()) % 2 == 0:
            mc.warning(SPINE_JNT_CNT_ODD_ERR)
            return False

        if not (self.ik_leg_chk_box.isChecked() or self.fk_leg_chk_box.isChecked()):
            mc.warning(IK_FK_LEG_ERR)
            return False

        if not (self.ik_arm_chk_box.isChecked() or self.fk_arm_chk_box.isChecked()):
            mc.warning(IK_FK_ARM_ERR)
            return False

        return True

    def ik_box_on_click(self, check_value, connect_box):
        """
        Function use to enable or disable the stretch arms/legs box, fired when IK arms/legs check box are clicked
        """
        if check_value is False:
            connect_box.setChecked(False)
            connect_box.setEnabled(False)
        else:
            connect_box.setEnabled(True)

    def create_rdo_grp_box(self, rdo_btn_list, title=None):
        """
        Create radio button group box
        """
        rdo_grp_box = QGroupBox(title)
        rdo_grp_layout = QHBoxLayout()
        for btn in rdo_btn_list:
            rdo_grp_layout.addWidget(btn)
        rdo_grp_box.setLayout(rdo_grp_layout)

        return rdo_grp_box

    def create_chk_box_grp(self, chk_box_list, title=None):
        """
        Create check box group
        """
        chk_box_grp = QGroupBox(title)
        chk_box_grp_layout = QVBoxLayout()
        for btn in chk_box_list:
            chk_box_grp_layout.addWidget(btn)
        chk_box_grp.setLayout(chk_box_grp_layout)

        return chk_box_grp

    def spine_count_val_changed(self):
        """
        Function that make sure the spine spin box value is an even number.
        """
        if self.spine_jnts_spin.value() % 2 == 0:
            current_val = self.spine_jnts_spin.value()
            if self.spine_jnts_val_before_changed > current_val:
                self.spine_jnts_spin.setValue(current_val-1)
            else:
                self.spine_jnts_spin.setValue(current_val + 1)

        self.spine_jnts_val_before_changed = self.spine_jnts_spin.value()


def main():
    ui = MainWindow()
    ui.init_ui()
