class TrustRentRouter:
    def db_for_read(self, model, **hints):
        return self._choose_db(model)

    def db_for_write(self, model, **hints):
        return self._choose_db(model)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Map apps to their databases
        if app_label == 'core' and db == 'core':
            return True
        elif app_label == 'ops' and db == 'ops':
            return True
        elif app_label == 'ledger' and db == 'ledger':
            return True
        return False  # Prevent accidental cross-writing

    def _choose_db(self, model):
        app_label = model._meta.app_label
        if app_label == 'core':
            return 'core'
        elif app_label == 'ops':
            return 'ops'
        elif app_label == 'ledger':
            return 'ledger'
        return None
