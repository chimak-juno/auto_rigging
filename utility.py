import maya.cmds as mc
import maya.api.OpenMaya as opm
import control_cuv_lib as ccl

SEPARATOR = "_"
SUFFIX_CONSTRAINT = "cst"


def create_ctr_cuv(pos=[0,0,0], rot=[0,0,0], match_obj=None, ctr_type="cube",
                   scale_cv=[10,10,10], rotate_cv=[0,0,0], move_cv=[0,0,0], ctr_name=None, space_name=None):
    """
    A common function to create control curve object, call by other create control function.
    """
    special_ctr_type = ["circle", "cog", "hip"]

    if ctr_type not in special_ctr_type:
        cvs = ccl.CUV_DICT[ctr_type]["cvs"]
        degree = ccl.CUV_DICT[ctr_type]["degree"]
        ctr = mc.curve(point=cvs, degree=degree)
    elif ctr_type == "circle":
        ctr = mc.circle(normal=(1,0,0))[0]
    elif ctr_type == "cog":
        ctr = get_cog_ctr_cuv()
    elif ctr_type == "hip":
        ctr = get_hip_ctr_cuv()

    ctr_grp = mc.group(ctr)

    if match_obj is not None:
        move_to_obj(ctr_grp, match_obj, maintain_rot=False)
    else:
        mc.move(pos[0], pos[1], pos[2], ctr_grp)
        mc.rotate(rot[0], rot[1], rot[2], ctr_grp)

    rotate_cvs(ctr, x=rotate_cv[0], y=rotate_cv[1], z=rotate_cv[2])
    scale_cvs(ctr, x=scale_cv[0], y=scale_cv[1], z=scale_cv[2])
    move_cvs(ctr, x=move_cv[0], y=move_cv[1], z=move_cv[2])

    if ctr_name is not None:
        ctr = mc.rename(ctr, ctr_name)

    if space_name is not None:
        ctr_grp = mc.rename(ctr_grp, space_name)
        ctr = get_child(ctr_grp)

    return ctr_grp, ctr


def get_cog_ctr_cuv():
    """
    Create a cog control curve.
    """
    circle_cuv = mc.circle(normal=(0, 1, 0))[0]
    even_cvs = mc.ls(circle_cuv+".cv[0]", circle_cuv+".cv[2]", circle_cuv+".cv[4]", circle_cuv+".cv[6]")
    scale_cvs = 0.3
    mc.scale(scale_cvs, scale_cvs, scale_cvs, even_cvs)
    return circle_cuv


def get_hip_ctr_cuv():
    """
    Create a hip control curve.
    """
    circle_cuv = mc.circle(normal=(0, 1, 0))[0]
    cvs = mc.ls(circle_cuv+".cv[3]", circle_cuv+".cv[7]")
    mc.move(0, 1, 0, cvs, relative=True, worldSpace=True)

    cvs = mc.ls(circle_cuv + ".cv[2]", circle_cuv + ".cv[0]", circle_cuv + ".cv[4]", circle_cuv + ".cv[6]")
    mc.move(0, 0.3, 0, cvs, relative=True, worldSpace=True)
    return circle_cuv

def rotate_obj(obj_name, x=0, y=0, z=0):
    """
    Rotate object based on the original rotation value.
    """
    obj_rot = mc.xform(obj_name, query=True, rotation=True)
    mc.xform(obj_name, rotation=(obj_rot[0]+x, obj_rot[1]+y, obj_rot[2]+z))


def rotate_cvs(obj_name, x=0, y=0, z=0):
    """
    Rotate object cvs based on the original rotation value.
    """
    cvs = mc.ls(obj_name + ".cv[*]")
    cvs_rot = mc.xform(cvs, query=True, rotation=True)
    mc.rotate(cvs_rot[0]+x, cvs_rot[1]+y, cvs_rot[2]+z, cvs)


def move_cvs(obj_name, x=0, y=0, z=0):
    """
    Rotate object cvs based on the original rotation value.
    """
    cvs = mc.ls(obj_name + ".cv[*]")
    cvs_trans = mc.xform(cvs, query=True, translation=True)
    mc.move(x, y, z, cvs, relative=True, localSpace=True)


def scale_cvs(obj_name, x=1, y=1, z=1):
    """
    Scale object cvs
    """
    cvs = mc.ls(obj_name + ".cv[*]")
    mc.scale(x, y, z, cvs)


def set_jnt_orient(original_jnt, target_jnt=None, add_rot=[0,0,0], affect_child=False):
    """
    Match two joint's joint orientation, original_jnt will follow target_jnt
    """
    child_list = mc.listRelatives(original_jnt, fullPath=True, noIntermediate=True)
    if child_list is not None:
        for i in range(len(child_list)):
            try:
                child_list[i] = mc.parent(child_list[i], world=True)[0]
            except:
                pass

    if target_jnt is not None:
        parent = mc.listRelatives(original_jnt, fullPath=True, parent=True)
        original_jnt = mc.parent(original_jnt, target_jnt)[0]
        mc.makeIdentity(original_jnt, rotate=True, jointOrient=True, apply=True)
        if parent is not None:
            original_jnt = mc.parent(original_jnt, parent)[0]
    else:
        jnt_rot = mc.xform(original_jnt, query=True, rotation=True)
        mc.rotate(jnt_rot[0]+add_rot[0], jnt_rot[1]+add_rot[1], jnt_rot[2]+add_rot[2], original_jnt)
        mc.makeIdentity(original_jnt, rotate=True, apply=True)

    if child_list is not None:
        for i in range(len(child_list)):
            try:
                child_list[i] = mc.parent(child_list[i], original_jnt)[0]
            except:
                pass

    return original_jnt


def get_distance(start_point, end_point):
    """
    Return the distance between 2 specific points
    """
    start_vec = opm.MVector(start_point)
    end_vec = opm.MVector(end_point)

    result_vec = end_vec - start_vec

    return result_vec.length()


def change_suffix(original_name, suffix):
    """
    Change the object suffix
    """
    result_name = original_name.split(SEPARATOR)[:-1]+[suffix]
    result_name = SEPARATOR.join(result_name)
    return result_name


def connect_with_md_node(driver, driven, connect_attr, x_value=None, y_value=None, z_value=None):
    """
    Connect two node through a multiple divide node, the connect_attr should only accept rotate and translate.
    """
    accepted_attr = ["rotate", "translate"]
    if connect_attr not in accepted_attr:
        print connect_attr + " attr is not accepted."
        return

    md_node = mc.createNode("multiplyDivide")

    if x_value is not None:
        mc.setAttr(md_node + ".input2X", x_value)
        mc.connectAttr(driver + "." + connect_attr + "X", md_node + ".input1X")
        mc.connectAttr(md_node + ".outputX", driven + "." + connect_attr + "X")
    if y_value is not None:
        mc.setAttr(md_node + ".input2Y", y_value)
        mc.connectAttr(driver + "." + connect_attr + "Y", md_node + ".input1Y")
        mc.connectAttr(md_node + ".outputY", driven + "." + connect_attr + "Y")
    if z_value is not None:
        mc.setAttr(md_node + ".input2Z", z_value)
        mc.connectAttr(driver + "." + connect_attr + "Z", md_node + ".input1Z")
        mc.connectAttr(md_node + ".outputZ", driven + "." + connect_attr + "Z")

    mc.setAttr(md_node + ".operation", 1)

    return md_node


def vec_abs(vector):
    """
    get the absolute value of a vector
    """
    return opm.MVector((abs(vector[0]), abs(vector[1]), abs(vector[2])))


def get_pole_vec_pos(start_point, mid_point, end_point):
    """
    Find the pole vector position
    """
    start_vec = opm.MVector(start_point)
    mid_vec = opm.MVector(mid_point)
    end_vec = opm.MVector(end_point)

    start_to_mid_vec = mid_vec - start_vec
    start_to_end_vec = end_vec - start_vec

    projection_vec = ((start_to_mid_vec*start_to_end_vec) / (vec_abs(start_to_end_vec)*vec_abs(start_to_end_vec))) * start_to_end_vec

    pole_vec = start_to_mid_vec - projection_vec

    pole_vec_len = pole_vec.length()

    if pole_vec_len > 0:
        scale_rate = start_to_mid_vec.length()/pole_vec.length()
    else:
        scale_rate = 1

    pole_vec = start_vec + projection_vec + pole_vec*scale_rate

    return [pole_vec[0], pole_vec[1], pole_vec[2]]


def move_to_obj(original_obj, target_obj, maintain_rot=False):
    """
    Move a object to other object position
    """
    target_pos = mc.xform(target_obj, query=True, translation=True, worldSpace=True)
    target_rot = mc.xform(target_obj, query=True, rotation=True, worldSpace=True)

    mc.move(target_pos[0], target_pos[1], target_pos[2], original_obj, absolute=True, worldSpace=True)

    if not maintain_rot:
        mc.rotate(target_rot[0], target_rot[1], target_rot[2], original_obj)


def split_jnt_chain(chain_root_jnt, span_count):
    """
    Split the joint chain to equal spans. Return a list of new joints(not including the root joint and end joint)
    """
    end_jnt = mc.listRelatives(chain_root_jnt, type="joint", allDescendents=True, noIntermediate=True, fullPath=True)[0]
    try:
        end_jnt = mc.parent(end_jnt, world=True)[0]
    except:
        pass
    aim_jnt([chain_root_jnt, end_jnt])

    mc.parent(end_jnt, chain_root_jnt)
    jnt_offset = mc.getAttr(end_jnt + ".translateX") / span_count

    end_jnt = mc.parent(end_jnt, world=True)[0]
    new_jnt_name_list = []
    for i in range(1, span_count):
        new_jnt_name = "inBtwJnt" + str(i + 1).zfill(2)
        offset_x = jnt_offset * i
        new_jnt_name = mc.joint(chain_root_jnt, position=(offset_x, 0, 0), relative=True, name=new_jnt_name)
        new_jnt_name_list.append(new_jnt_name)

        if i > 1:
            mc.parent(new_jnt_name, new_jnt_name_list[i - 2])

    mc.parent(end_jnt, new_jnt_name_list[-1])

    return new_jnt_name_list


def aim_jnt(jnt_list):
    """
    Input a joint list, function will aim the joint one by one, the first one will aim to the second one, the second one
    will aim to the third one, so far and so forth..
    """
    for i, jnt in enumerate(jnt_list):
        if i < len(jnt_list)-1:
            target_jnt = jnt_list[i+1]
            to_aim_jnt = jnt
            freeze_jnt_rot(to_aim_jnt)
            temp_aim_cst = mc.aimConstraint(target_jnt, to_aim_jnt, maintainOffset=False)
            mc.delete(temp_aim_cst)
            freeze_jnt_rot(to_aim_jnt)


def freeze_jnt_rot(jnt_name):
    """
    Zero out the rotation(Not the joint rotation), if there is a value other than 0, function will put the value on joint rotation
    """
    mc.makeIdentity(jnt_name, rotate=True, apply=True)


def create_ik_limb(root_jnt, mid_jnt, end_jnt, ik_ctr_type="square", pv_ctr_type="square",
                   constraint_ik_ctr=True, constraint_pv_ctr=True, ik_ctr_rotate=[0,0,0],
                   pv_ctr_rotate=[90,0,0], ik_ctr_scale =[10,10,10], pv_ctr_scale =[10,10,10],
                   match_jnt_orient=False):
    """
    Create ik joints, ik control, pole vector control for the input joints.
    """
    root_ik = mc.duplicate(root_jnt, name="root_ik", parentOnly=True)[0]
    mid_ik = mc.duplicate(mid_jnt, name="mid_ik", parentOnly=True)[0]
    end_ik = mc.duplicate(end_jnt, name="end_ik", parentOnly=True)[0]

    root_ik_pos = mc.xform(root_ik, query=True, translation=True, worldSpace=True)
    mid_ik_pos = mc.xform(mid_ik, query=True, translation=True, worldSpace=True)
    end_ik_pos = mc.xform(end_ik, query=True, translation=True, worldSpace=True)

    end_ik = mc.parent(end_ik, mid_ik)[0]
    mid_ik = mc.parent(mid_ik, root_ik)[0]

    ik_hdl = mc.ikHandle(startJoint=root_ik, endEffector=end_ik)[0]
    pole_vec_pos = get_pole_vec_pos(start_point=root_ik_pos, mid_point=mid_ik_pos, end_point=end_ik_pos)

    end_jnt_pos = mc.xform(end_ik, query=True, translation=True, worldSpace=True)
    if match_jnt_orient is True:
        ik_ctr_grp, ik_ctr = create_ctr_cuv(match_obj=end_ik, ctr_type=ik_ctr_type, rotate_cv=ik_ctr_rotate, scale_cv=ik_ctr_scale)
    else:
        ik_ctr_grp, ik_ctr = create_ctr_cuv(pos=end_jnt_pos, ctr_type=ik_ctr_type, rotate_cv=ik_ctr_rotate, scale_cv=ik_ctr_scale)

    pv_ctr_grp, pv_ctr = create_ctr_cuv(pos=pole_vec_pos, ctr_type=pv_ctr_type, rotate_cv=pv_ctr_rotate, scale_cv=pv_ctr_scale)

    hide_attr(ik_ctr, attrs=["scale", "visibility"])
    hide_attr(pv_ctr, attrs=["scale", "visibility"])

    if constraint_ik_ctr is True:
        mc.parentConstraint(ik_ctr, ik_hdl)
        mc.orientConstraint(ik_ctr, end_ik)
    if constraint_pv_ctr is True:
        mc.poleVectorConstraint(pv_ctr, ik_hdl)

    # return the ik joint chain, ik handler, ik, pv control space groups and controls
    return [root_ik, mid_ik, end_ik], ik_hdl, ik_ctr_grp, ik_ctr, pv_ctr_grp, pv_ctr


def create_space_grp(target=None, target_list=None, suffix="nul"):
    if target_list is None:
        target_list = [target]

    for obj in target_list:
        obj_parent = mc.listRelatives(obj, fullPath=True, parent=True)
        grp = mc.group(name=change_suffix(clear_path(obj), suffix), empty=True)
        move_to_obj(grp, obj)
        mc.parent(obj, grp)[0]
        if obj_parent is not None:
            grp = mc.parent(grp, obj_parent)

    return grp, obj


def create_fk_limb(jnt_chain, ctr_scale=[10,10,10], add_offset=False):
    """
    Create fk joints, fk controls for the input joint chain.
    """
    fk_jnt_chain = []
    for i, jnt in enumerate(jnt_chain):
        fk_jnt = mc.duplicate(jnt, name="fk"+str(i+1).zfill(2), parentOnly=True)[0]
        fk_jnt_chain.append(fk_jnt)
        if i > 0:
            fk_jnt_chain[i] = mc.parent(fk_jnt_chain[i], fk_jnt_chain[i-1])[0]

    fk_ctr_space_list, fk_ctr_list = create_fk_ctrs(fk_jnt_chain,  ctr_scale=[10,10,10], add_offset=add_offset)

    return fk_jnt_chain, fk_ctr_space_list, fk_ctr_list


def create_fk_ctrs(fk_jnt_chain, ctr_scale=[10,10,10], add_offset=False):
    """
    Add fd controls to the input fk joints chain.
    """
    fk_ctr_list = []
    fk_ctr_space_list = []
    fk_ctr_offset_list = []
    return_list = [fk_ctr_space_list, fk_ctr_list]

    for i, fk_jnt in enumerate(fk_jnt_chain):
        fk_ctr_space, fk_ctr = create_ctr_cuv(match_obj=fk_jnt, ctr_type="circle", scale_cv=ctr_scale)
        if add_offset is True:
            offset_grp = mc.group(fk_ctr)
            fk_ctr_offset_list.append(offset_grp)

        cst = mc.orientConstraint(fk_ctr, fk_jnt, maintainOffset=True)
        hide_attr(fk_ctr, attrs=["translate", "scale", "visibility"])
        #mc.rename(cst, change_suffix(clear_path(fk_jnt), SUFFIX_CONSTRAINT))

        if i > 0:
            fk_ctr_space = mc.parent(fk_ctr_space, fk_ctr_list[i-1])[0]

        fk_ctr_list.append(fk_ctr)
        fk_ctr_space_list.append(fk_ctr_space)

    if add_offset is True:
        return_list.append(fk_ctr_offset_list)

    return return_list


def hide_attr(obj, attrs=["translate", "rotate", "scale", "visibility"], lock_attr=True):
    """
    Hide and lock the attributes in attrs list
    """
    for obj_attr in mc.listAttr(obj, keyable=True):
        for hide_attr in attrs:
            if hide_attr in obj_attr:
                mc.setAttr(obj+"."+obj_attr, keyable=False, lock=lock_attr)


def create_stretch_limb(ik_ctr, end_jnt, stretch_jnt_list, switch_ctr, switch_attr_name, global_ctr):
    """
    Create stretch limb based on the input stretch jnt list,
    """
    ik_ctr_pos = mc.xform(ik_ctr, query=True, translation=True, worldSpace=True)
    end_jnt_pos = mc.xform(end_jnt, query=True, translation=True, worldSpace=True)

    end_loc = mc.spaceLocator()
    move_to_obj(end_loc, target_obj=ik_ctr, maintain_rot=True)

    distance_dimen_shape = mc.distanceDimension(startPoint=ik_ctr_pos, endPoint=end_jnt_pos)
    start_loc, end_loc = mc.listConnections(distance_dimen_shape)

    mc.pointConstraint(ik_ctr, start_loc)
    mc.pointConstraint(end_jnt, end_loc)

    distance = mc.getAttr(distance_dimen_shape+".distance")

    md_node = mc.createNode("multiplyDivide", name=switch_attr_name+SEPARATOR+"md")
    mc.setAttr(md_node+".operation", 2)
    mc.connectAttr(distance_dimen_shape+".distance", md_node+".input1X")

    global_scale_md = mc.createNode("multiplyDivide", name=switch_attr_name+"Scale"+SEPARATOR+"md")
    mc.setAttr(global_scale_md + ".operation", 1)
    mc.connectAttr(global_ctr + ".scaleX", global_scale_md + ".input1X")
    mc.setAttr(global_scale_md + ".input2X", distance)
    mc.connectAttr(global_scale_md + ".outputX", md_node + ".input2X")

    stretch_condi_node = mc.createNode("condition", name=switch_attr_name+"Trigger"+SEPARATOR+"condi")
    mc.setAttr(stretch_condi_node + ".operation", 2)
    mc.setAttr(stretch_condi_node + ".secondTerm", 1)
    mc.connectAttr(md_node + ".outputX", stretch_condi_node+".firstTerm")
    mc.connectAttr(md_node + ".outputX", stretch_condi_node + ".colorIfTrueR")

    mc.addAttr(switch_ctr, longName=switch_attr_name, attributeType='short', keyable=True, maxValue=1, minValue=0)
    switch_condi_node = mc.createNode("condition", name=switch_attr_name+"Switch"+SEPARATOR+"condi")
    mc.setAttr(switch_condi_node + ".operation", 0)
    mc.setAttr(switch_condi_node + ".secondTerm", 1)
    mc.connectAttr(switch_ctr + "." + switch_attr_name, switch_condi_node+".firstTerm")
    mc.connectAttr(stretch_condi_node + ".outColorR", switch_condi_node + ".colorIfTrueR")

    for stretch_jnt in stretch_jnt_list:
        mc.connectAttr(switch_condi_node + ".outColorR", stretch_jnt + ".scaleX")

    return mc.listRelatives(distance_dimen_shape, parent=True), start_loc, end_loc


def clear_path(obj_name):
    """
    Clear the path string for the input object name.
    """
    return obj_name.split("|")[-1]


def get_child(obj_name):
    return mc.ls(mc.listRelatives(obj_name, fullPath=True), transforms=True)[0]








