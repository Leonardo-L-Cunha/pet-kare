from rest_framework.views import APIView, Request, Response , status
from rest_framework.pagination import PageNumberPagination
from pets.serializers import PetSerializer
from .models import Pet
from groups.models import Group
from traits.models import Trait
from django.shortcuts import get_object_or_404

class PetView(APIView, PageNumberPagination):

    def get(self, request:Request) -> Response:
        pets = Pet.objects.all()
        trait = request.query_params.get("trait",None)

        if trait:
             trait_filter = Trait.objects.filter(name = trait)
             if trait_filter.exists():
                pets = pets.filter(traits=trait_filter.first())
       
        result_page = self.paginate_queryset(pets,request,view=self)
        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)
    def post(self, request:Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = serializer.validated_data.pop('group')
        traits = serializer.validated_data.pop('traits')
        
        group_obj = Group.objects.filter(
                scientific_name__iexact = group["scientific_name"]
        ).first()

        if not group_obj:
            group_obj = Group.objects.create(**group)
       
        serializer.validated_data["group"] = group_obj
    
        pet_obj = Pet.objects.create(**serializer.validated_data)

        for trait_dict in traits:
            traits_obj = Trait.objects.filter(
                name__iexact=trait_dict['name']
            ).first()

            if not traits_obj:
                traits_obj = Trait.objects.create(**trait_dict)
            pet_obj.traits.add(traits_obj)
        
        serializer = PetSerializer(pet_obj)                
        
        return Response(serializer.data,status.HTTP_201_CREATED)

class PetViewDetail(APIView):
    def get(self, request:Request,pet_id):
        pets = get_object_or_404(Pet,id=pet_id)

        serializer = PetSerializer(pets)
        return Response(serializer.data, status.HTTP_200_OK)
    
    def patch(self, request:Request, pet_id):
        pets = get_object_or_404(Pet,id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

   
        group_data:dict = serializer.validated_data.pop("group",None)
        trait_data:dict = serializer.validated_data.pop("traits",None)
        
        if group_data:
            try:
                group_obj = Group.objects.filter(
                    scientific_name__iexact = group_data["scientific_name"]
                 ).first()

                if not group_obj:
                    group_obj = Group.objects.create(**group_data)
       
                serializer.validated_data["group"] = group_obj
                for key, value in group_data.items():
                    setattr(group_obj,key,value)

                pets.group.save()

            except Pet.group.RelatedObjectDoesNotExist:
                Group.objects.create(**group_data,pets=pets)

        
        if trait_data:
            existing_traits = {}
            new_traits = []
            for trait in trait_data:
                trait_name = trait.get('name')
                if trait_name:
                    existing_trait = Trait.objects.filter(name__iexact=trait_name).first()
                    if existing_trait:
                        existing_traits[trait_name] = existing_trait
                    else:
                        new_trait = Trait.objects.create(name=trait_name)
                        new_traits.append(new_trait)

            
            pets.traits.set(existing_traits.values())
            pets.traits.add(*new_traits)
                          
           
        for key, value in serializer.validated_data.items():
                    setattr(pets,key,value)
        pets.save()
        serializer = PetSerializer(pets)
        return Response(serializer.data,status.HTTP_200_OK)
    
    def delete(self, request:Request, pet_id):
        pets = get_object_or_404(Pet,id=pet_id)

        pets.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)