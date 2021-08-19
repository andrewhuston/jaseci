"""
Mix in for jac code object in Jaseci
"""
import json
from jaseci.utils.utils import logger
from jaseci.jac.ir.ast import ast


class jac_json_enc(json.JSONEncoder):
    """Custom Json encoder for Jac ASTs"""

    def default(self, obj):
        if(isinstance(obj, ast)):
            return obj.__dict__
        return super().default(obj)


class jac_json_dec(json.JSONDecoder):
    """Custom hook for decoding Jac ASTs"""

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):

        if isinstance(obj, dict):
            if "start_rule" in obj and "kid" in obj:
                ret = ast()
                for i in ret.__dict__.keys():
                    setattr(ret, i, obj[i])
                return ret

        if isinstance(obj, dict):
            for key in list(obj):
                obj[key] = self.object_hook(obj[key])
            return obj

        if isinstance(obj, list):
            for i in range(0, len(obj)):
                obj[i] = self.object_hook(obj[i])
            return obj

        return obj


class jac_code():
    """Obj mixin to code pickling"""

    def __init__(self, code_ir=None):
        self.is_active = False
        self.code_ir = None
        self._jac_ast = None
        self.apply_ir(code_ir)

    def reset(self):
        self.is_active = False

    def apply_ir(self, ir):
        """Apply's IR to object"""
        self.code_ir = ir if(isinstance(ir, str)) else \
            json.dumps(cls=jac_json_enc, obj=ir)
        self._jac_ast = json.loads(
            cls=jac_json_dec, s=self.code_ir) if ir else None
        if(self._jac_ast):
            kid = self._jac_ast.kid
            if(self.j_type != 'sentinel'):
                self.kind = f"{kid[0].token_text()}"
                self.name = f"{kid[1].token_text()}"
        self.save()

    def parse_jac(self, code, start_rule='start'):
        """Generate AST tree from Jac code text"""
        logger.info(str(f'{self.name}: Processing Jac code...'))
        tree = ast(jac_text=code, start_rule=start_rule)
        if(tree.parse_errors):
            logger.error(str(f'{self.name}: Invalid syntax in Jac code!'))
            for i in tree.parse_errors:
                logger.error(i)
            return None
        return tree

    def register(self, code):
        """
        Parses Jac code and saves IR
        """
        start_rule = 'start' if self.j_type == 'sentinel' \
            else self.j_type
        tree = self.parse_jac(code, start_rule=start_rule)

        if(not tree):
            self.is_active = False
        else:
            self.apply_ir(tree)
            self.is_active = True

        if(self.is_active):
            logger.info(str(f'{self.name}: Successfully registered code'))
        else:
            logger.info(str(f'{self.name}: Code not registered'))
        return self.is_active

    def ir_dict(self):
        """Return IR as dictionary"""
        return json.loads(self.code_ir)
