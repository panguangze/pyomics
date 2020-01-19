from pyomics.operator import executor as ex
op = ex.OperatorsExecutor()
op.add_operator("test.py")
op.execute()