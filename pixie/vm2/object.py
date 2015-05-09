import rpython.rlib.jit as jit

class Object(object):
    """ Base Object for all VM objects
    """
    _attrs_ = ()

    def type(self):
        affirm(False, u".type isn't overloaded")

    @jit.unroll_safe
    def invoke(self, args):
        #TODO: fix
        runtime_error(u"bad invoke")
        #import pixie.vm.stdlib as stdlib
        #return stdlib.invoke_other(self, args)

    def int_val(self):
        affirm(False,  u"Expected Number, not " + self.type().name())
        return 0

    def r_uint_val(self):
        affirm(False, u"Expected Number, not " + self.type().name())
        return 0

    def hash(self):
        import pixie.vm.rt as rt
        return rt.wrap(compute_identity_hash(self))

    def promote(self):
        return self

class TypeRegistry(object):
    def __init__(self):
        self._types = {}
        self._ns_registry = None

    def register_type(self, nm, tp):
        if self._ns_registry is None:
            self._types[nm] = tp
        else:
            self.var_for_type_and_name(nm, tp)

    def var_for_type_and_name(self, nm, tp):
        splits = nm.split(u".")
        size = len(splits) - 1
        assert size >= 0
        ns = u".".join(splits[:size])
        name = splits[size]
        var = self._ns_registry.find_or_make(ns).intern_or_make(name)
        var.set_root(tp)
        return var

    def set_registry(self, registry):
        self._ns_registry = registry
        for nm in self._types:
            tp = self._types[nm]
            self.var_for_type_and_name(nm, tp)


    def get_by_name(self, nm, default=None):
        return self._types.get(nm, default)

_type_registry = TypeRegistry()

def get_type_by_name(nm):
    return _type_registry.get_by_name(nm)

class Type(Object):
    def __init__(self, name, parent=None, object_inited=True):
        assert isinstance(name, unicode), u"Type names must be unicode"
        _type_registry.register_type(name, self)
        self._name = name

        if object_inited:
            if parent is None:
                parent = Object._type

            parent.add_subclass(self)

        self._parent = parent
        self._subclasses = []

    def name(self):
        return self._name

    def type(self):
        return Type._type

    def add_subclass(self, tp):
        self._subclasses.append(tp)

    def subclasses(self):
        return self._subclasses

Object._type = Type(u"pixie.stdlib.Object", None, False)
Type._type = Type(u"pixie.stdlib.Type")

@jit.elidable_promote()
def istypeinstance(obj, t):
    obj_type = obj.type()
    assert isinstance(obj_type, Type)
    if obj_type is t:
        return True
    elif obj_type._parent is not None:
        obj_type = obj_type._parent
        while obj_type is not None:
            if obj_type is t:
                return True
            obj_type = obj_type._parent
        return False
    else:
        return False

class Continuation(object):
    should_enter_jit = False
    _immutable_ = True
    def call_continuation(self, val, stack):
        return None, stack

    def get_ast(self):
        from pixie.vm2.primitives import nil
        return nil


class StackCell(object):
    """Defines an immutable call stack, stacks can be copied, spliced and combined"""
    _immutable_fields_ = ["_parent", "_cont"]
    def __init__(self, cont, parent_stack):
        self._parent = parent_stack
        self._cont = cont

def stack_cons(stack, other):
    return StackCell(other, stack)


from rpython.rlib.jit import JitDriver
jitdriver = JitDriver(greens=["ast"], reds=["stack", "val", "cont"])

def run_stack(val, cont, stack=None):
    stack = None
    val = None
    ast = cont.get_ast()
    while True:
        jitdriver.jit_merge_point(ast=ast, stack=stack, val=val, cont=cont)
        val, stack = cont.call_continuation(val, stack)
        if stack is None:
            return val
        old_cont = cont
        old_ast = old_cont.get_ast()
        cont = stack._cont
        ast = cont.get_ast()
        stack = stack._parent
        #print ast
        if old_cont.should_enter_jit:
            jitdriver.can_enter_jit(ast=old_ast, stack=stack, val=val, cont=cont)

    return val




## TODO: fix
def affirm(f, msg):
    if not f:
        print msg
        raise NotImplementedError()

def runtime_error(msg, kw=None):
    raise NotImplementedError()

class WrappedException(BaseException):
    pass