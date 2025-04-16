class TrustRentRouter:
    def db_for_read(self, model, **hints):
        # For test cases, use the default database
        if hasattr(model, '_state') and hasattr(model._state, 'db'):
            if model._state.db:
                return model._state.db
        return self._choose_db(model)

    def db_for_write(self, model, **hints):
        # For test cases, use the default database
        if hasattr(model, '_state') and hasattr(model._state, 'db'):
            if model._state.db:
                return model._state.db
        return self._choose_db(model)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # For test database, allow all migrations
        if 'test' in db:
            return True
        # Map apps to their databases
        if app_label == 'core' and db in ['core', 'default']:
            return True
        elif app_label == 'ops' and db == 'ops':
            return True
        elif app_label == 'ledger' and db == 'ledger':
            return True
        elif app_label in ['auth', 'contenttypes', 'sessions'] and db == 'default':
            return True
        return False  # Prevent accidental cross-writing

    def allow_relation(self, obj1, obj2, **hints):
        # Allow all relations in test environment
        if hasattr(obj1, '_state') and hasattr(obj2, '_state'):
            if getattr(obj1._state, 'db', None) and 'test' in obj1._state.db:
                return True
            if getattr(obj2._state, 'db', None) and 'test' in obj2._state.db:
                return True
        # Allow relations between objects in the same database
        # or between core and other databases
        db1 = self._choose_db(obj1._meta.model)
        db2 = self._choose_db(obj2._meta.model)
        if db1 == db2:
            return True
        if 'core' in [db1, db2]:
            return True
        return False

    def _choose_db(self, model):
        app_label = model._meta.app_label
        if app_label == 'core':
            return 'core'
        elif app_label == 'ops':
            return 'ops'
        elif app_label == 'ledger':
            return 'ledger'
        elif app_label in ['auth', 'contenttypes', 'sessions']:
            return 'default'
        return None
