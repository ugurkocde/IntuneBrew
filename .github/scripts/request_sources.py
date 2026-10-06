"""Source identities and package recipes supported by app request fulfillment."""
FORMULA_RECIPES = {"azure-cli": "azure-cli-universal-v1"}
CASK_RECIPES = {"logi-options+": "logi-options-silent-v1"}


def source_token(data):
    return data.get("homebrew_cask") or data.get("homebrew_formula") or data.get("custom_source")


def required_recipe(token):
    return FORMULA_RECIPES.get(token) or CASK_RECIPES.get(token)


def fulfilled_recipe(data):
    expected = required_recipe(source_token(data))
    return not expected or (data.get("packaging_recipe") == expected and data.get("type") == "app")
