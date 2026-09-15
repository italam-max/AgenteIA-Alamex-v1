"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import type { ProductPhoto } from "@/lib/types";

export function ProductPhotosEditor() {
  const [photos, setPhotos] = useState<ProductPhoto[] | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  function reload() {
    fetch("/api/config/product-photos")
      .then((res) => res.json())
      .then(setPhotos);
  }

  useEffect(reload, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>Fotos de producto</CardTitle>
          <CardDescription>
            Fotos reales que el agente prefiere usar en vez de generar con IA cuando el tema calza
            con los <code>tags</code>.
          </CardDescription>
        </div>
        <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
          <DialogTrigger render={<Button variant="outline" size="sm" />}>+ Agregar foto</DialogTrigger>
          <UploadPhotoDialog
            onUploaded={() => {
              setUploadOpen(false);
              reload();
            }}
          />
        </Dialog>
      </CardHeader>
      <CardContent>
        {photos === null ? (
          <Skeleton className="h-64 w-full" />
        ) : photos.length === 0 ? (
          <p className="text-sm text-muted-foreground">Todavía no hay fotos registradas.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {photos.map((photo) => (
              <PhotoCard key={photo.filename} photo={photo} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PhotoCard({ photo }: { photo: ProductPhoto }) {
  const [tags, setTags] = useState(photo.tags.join(", "));
  const [description, setDescription] = useState(photo.description);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const res = await fetch(`/api/config/product-photos/${encodeURIComponent(photo.filename)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
          description,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al guardar");
      toast.success(`${photo.filename} actualizada.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="overflow-hidden">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/api/product-photo/${encodeURIComponent(photo.filename)}`}
        alt={photo.description}
        className="aspect-square w-full bg-muted object-cover"
      />
      <CardContent className="space-y-2 pt-4">
        <p className="truncate text-xs font-mono text-muted-foreground">{photo.filename}</p>
        <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tags separados por coma" />
        <Textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="descripción"
          className="h-20 text-sm"
        />
      </CardContent>
      <CardFooter>
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? "Guardando..." : "Guardar"}
        </Button>
      </CardFooter>
    </Card>
  );
}

function UploadPhotoDialog({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [tags, setTags] = useState("");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tags", tags);
      formData.append("description", description);
      const res = await fetch("/api/config/product-photos/upload", { method: "POST", body: formData });
      if (!res.ok) throw new Error((await res.json()).error ?? "Error al subir");
      toast.success("Foto retocada y agregada.");
      onUploaded();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error al subir");
    } finally {
      setUploading(false);
    }
  }

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Agregar foto de producto</DialogTitle>
        <DialogDescription>
          Se recorta el producto de su fondo y se compone sobre un fondo de estudio limpio
          (rembg — determinístico, no altera el producto). Tarda ~30-90s.
        </DialogDescription>
      </DialogHeader>
      <div className="space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="upload-file">Foto (jpg/png)</Label>
          <Input id="upload-file" type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="upload-tags">Tags (separados por coma)</Label>
          <Input id="upload-tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="MRL-G, cabina, interior" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="upload-description">Descripción</Label>
          <Textarea id="upload-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
      </div>
      <DialogFooter>
        <Button onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? "Retocando..." : "Subir y retocar"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}
