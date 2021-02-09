import bpy


class ApplyOperatorsOperator(bpy.types.Operator):
    """Apply operators on selected objects."""
    bl_idname = "dusty.applyoperators"
    bl_label = "Apply operators"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        # execute() is called when running the operator.
        selected_objects = bpy.context.selected_objects
        for selected_object in selected_objects:
            bpy.context.view_layer.objects.active = selected_object
            print(selected_object.name)
            new_context = bpy.context.copy()
            new_context['selected_objects'] = [selected_object]
            new_context['active_object'] = selected_object
            for modifier in selected_object.modifiers:
                print(modifier.name)
                bpy.ops.object.modifier_apply(new_context, "INVOKE_DEFAULT", False, modifier=modifier.name)

        self.report({'INFO'}, f"Applied operators.")
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
