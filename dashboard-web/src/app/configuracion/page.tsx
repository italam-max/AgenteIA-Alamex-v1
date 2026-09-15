"use client";

import { FeaturedModelEditor } from "@/components/config/FeaturedModelEditor";
import { GuidelinesEditor } from "@/components/config/GuidelinesEditor";
import { PlatformsEditor } from "@/components/config/PlatformsEditor";
import { ProductPhotosEditor } from "@/components/config/ProductPhotosEditor";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ConfiguracionPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Configuración</h1>
        <p className="text-sm text-muted-foreground">
          Ajustes superficiales de los agentes — cambian el comportamiento en la próxima corrida,
          sin tocar código.
        </p>
      </div>

      <Tabs defaultValue="tono">
        <TabsList variant="line" className="border-b border-border">
          <TabsTrigger value="tono">Tono de marca</TabsTrigger>
          <TabsTrigger value="plataformas">Plataformas y generador</TabsTrigger>
          <TabsTrigger value="destacado">Modelo destacado</TabsTrigger>
          <TabsTrigger value="fotos">Fotos de producto</TabsTrigger>
        </TabsList>
        <TabsContent value="tono" className="mt-4">
          <GuidelinesEditor />
        </TabsContent>
        <TabsContent value="plataformas" className="mt-4">
          <PlatformsEditor />
        </TabsContent>
        <TabsContent value="destacado" className="mt-4">
          <FeaturedModelEditor />
        </TabsContent>
        <TabsContent value="fotos" className="mt-4">
          <ProductPhotosEditor />
        </TabsContent>
      </Tabs>
    </div>
  );
}
