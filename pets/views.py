
from rest_framework.views import APIView, status, Request, Response
from pets.models import Pet
from traits.models import Trait
from groups.models import Group
from pets.serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        group_data = serializer.validated_data.pop("group")
        try:
            group = Group.objects.get(scientific_name__exact=group_data["scientific_name"])
        except Group.DoesNotExist:
            group = Group.objects.create(**group_data)
        traits = serializer.validated_data.pop("traits")
        pet = Pet.objects.create(**serializer.validated_data, group=group)
        for traits_data in traits:
            try:
                trait = Trait.objects.get(name__iexact=traits_data["name"])
            except Trait.DoesNotExist:
                trait = Trait.objects.create(**traits_data)
            pet.traits.add(trait)
        serializer = PetSerializer(pet)
        return Response(serializer.data, status.HTTP_201_CREATED)

    def get(self, request: Request) -> Response:
        by_trait = request.query_params.get("trait", None)
        if by_trait:
            pets = Pet.objects.filter(traits__name__icontains=by_trait)
        else:
            pets = Pet.objects.all().order_by("id")
        result_page = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id) -> Response:
        found_pet = get_object_or_404(Pet, pk=pet_id)
        serializer = PetSerializer(found_pet)
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id) -> Response:
        found_pet = get_object_or_404(Pet, pk=pet_id)
        found_pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def patch(self, request: Request, pet_id) -> Response:
        found_pet = get_object_or_404(Pet, pk=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        group_data = serializer.validated_data.pop("group", "")
        if group_data:
            try:
                group = Group.objects.get(scientific_name__exact=group_data["scientific_name"])
            except Group.DoesNotExist:
                group = Group.objects.create(**group_data)
            found_pet.group = group
        traits = serializer.validated_data.pop("traits", "")
        if traits:

            found_pet.traits.clear()
            for traits_data in traits:
                try:
                    trait = Trait.objects.get(name__iexact=traits_data["name"])
                except Trait.DoesNotExist:
                    trait = Trait.objects.create(**traits_data)
                found_pet.traits.add(trait)
        for k, v in serializer.validated_data.items():
            setattr(found_pet, k, v)
        found_pet.save()
        serializer = PetSerializer(found_pet)
        return Response(serializer.data)


