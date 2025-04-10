from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    account_name = 'chefquizstorage' # Must be replaced by your <storage_account_name>
    account_key = 'etp9cUTT4JUeSfipF6P59qDfoi9ArALV7LI0VBcRlXenHI7m05VVaiCU8t2wev2RRypqSq4+lIeq+ASt0Ry3aA==' # Must be replaced by your <storage_account_key>
    azure_container = 'media'
    expiration_secs = None

class AzureStaticStorage(AzureStorage):
    account_name = 'chefquizstorage' # Must be replaced by your storage_account_name
    account_key = 'etp9cUTT4JUeSfipF6P59qDfoi9ArALV7LI0VBcRlXenHI7m05VVaiCU8t2wev2RRypqSq4+lIeq+ASt0Ry3aA==' # Must be replaced by your <storage_account_key>
    azure_container = 'static'
    expiration_secs = None