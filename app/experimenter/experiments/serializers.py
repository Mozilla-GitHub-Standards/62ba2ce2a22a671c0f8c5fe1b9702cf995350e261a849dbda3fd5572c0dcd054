import decimal
import time

from rest_framework import serializers

from experimenter.base.models import Country, Locale
from experimenter.experiments.models import Experiment, ExperimentVariant


class JSTimestampField(serializers.Field):
    """
    Serialize a datetime object into javascript timestamp
    ie unix time in ms
    """

    def to_representation(self, obj):
        if obj:
            return time.mktime(obj.timetuple()) * 1000
        else:
            return None


class ExperimentVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = (
            "description",
            "is_control",
            "name",
            "ratio",
            "slug",
            "value",
        )


class ExperimentRecipeVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExperimentVariant
        fields = ("ratio", "slug", "value")


class LocalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Locale
        fields = ("code", "name")


class CountriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ("code", "name")


class ExperimentSerializer(serializers.ModelSerializer):
    start_date = JSTimestampField()
    end_date = JSTimestampField()
    proposed_start_date = JSTimestampField()
    variants = ExperimentVariantSerializer(many=True)
    locales = LocalesSerializer(many=True)
    countries = CountriesSerializer(many=True)

    class Meta:
        model = Experiment
        fields = (
            "experiment_url",
            "type",
            "name",
            "slug",
            "short_description",
            "client_matching",
            "locales",
            "countries",
            "start_date",
            "end_date",
            "population",
            "population_percent",
            "firefox_channel",
            "firefox_version",
            "objectives",
            "analysis_owner",
            "analysis",
            "addon_name",
            "addon_experiment_id",
            "addon_testing_url",
            "addon_release_url",
            "pref_branch",
            "pref_key",
            "pref_type",
            "proposed_start_date",
            "proposed_enrollment",
            "proposed_duration",
            "variants",
        )


class FilterObjectBucketSample(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    input = serializers.ReadOnlyField(
        default=["normandy.recipe.id", "normandy.userId"]
    )
    start = serializers.ReadOnlyField(default=0)
    count = serializers.SerializerMethodField()
    total = serializers.ReadOnlyField(default=1000)

    class Meta:
        model = Experiment
        fields = ("type", "input", "start", "count", "total")

    def get_type(self, obj):
        return "bucketSample"

    def get_count(self, obj):
        return int(obj.population_percent * 10)


class FilterObjectChannel(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "channels")

    def get_type(self, obj):
        return "channel"

    def get_channels(self, obj):
        return [obj.firefox_channel.lower()]


class FilterObjectLocale(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    locales = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "locales")

    def get_type(self, obj):
        return "locale"

    def get_locales(self, obj):
        return list(obj.locales.all().values_list("code"))


class FilterObjectCountry(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ("type", "countries")

    def get_type(self, obj):
        return "country"

    def get_countries(self, obj):
        return list(obj.countries.all().values_list("code"))


class ExperimentRecipePrefArgumentsSerializer(serializers.ModelSerializer):
    preferenceBranchType = serializers.ReadOnlyField(source="pref_branch")
    slug = serializers.ReadOnlyField(source="normandy_slug")
    experimentDocumentUrl = serializers.ReadOnlyField(source="experiment_url")
    preferenceName = serializers.ReadOnlyField(source="pref_key")
    preferenceType = serializers.ReadOnlyField(source="pref_type")
    branches = ExperimentRecipeVariantSerializer(many=True, source="variants")

    class Meta:
        model = Experiment
        fields = (
            "preferenceBranchType",
            "slug",
            "experimentDocumentUrl",
            "preferenceName",
            "preferenceType",
            "branches",
        )


class ExperimentRecipeAddonArgumentsSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="addon_experiment_id")

    class Meta:
        model = Experiment
        fields = ("name",)


class ExperimentRecipeSerializer(serializers.ModelSerializer):
    action_name = serializers.SerializerMethodField()
    filter_object = serializers.SerializerMethodField()
    extra_filter_expression = serializers.ReadOnlyField(
        source="client_matching"
    )
    arguments = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = (
            "action_name",
            "name",
            "filter_object",
            "extra_filter_expression",
            "arguments",
        )

    def get_action_name(self, obj):
        if obj.is_pref_study:
            return "preference-experiment"
        elif obj.is_addon_study:
            return "opt-out-study"

    def get_filter_object(self, obj):
        filter_objects = [
            FilterObjectBucketSample(obj).data,
            FilterObjectChannel(obj).data,
        ]

        if obj.locales:
            filter_objects.append(FilterObjectLocale(obj).data)

        if obj.countries:
            filter_objects.append(FilterObjectCountry(obj).data)

        return filter_objects

    def get_arguments(self, obj):
        if obj.is_pref_study:
            return ExperimentRecipePrefArgumentsSerializer(obj).data
        elif obj.is_addon_study:
            return ExperimentRecipeAddonArgumentsSerializer(obj).data
