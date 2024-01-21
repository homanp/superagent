"use client"

import Image from "next/image"
import { useAsync } from "react-use"

import { siteConfig } from "@/config/site"
import { Api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

function Loading() {
  return (
    <div className="flex flex-col space-y-4">
      {Array(5).fill(<Skeleton className="h-[80px] w-full" />)}
    </div>
  )
}

export default function Storage({ profile }: { profile: any }) {
  const api = new Api(profile.api_key)
  const { value, loading } = useAsync(async () => {
    const { data } = await api.getVectorDbs()
    return data
  }, [])

  return (
    <div className="container flex max-w-4xl flex-col space-y-10 pt-10">
      <div className="flex flex-col">
        <p className="text-lg font-medium">Storage</p>
        <p className="text-muted-foreground">
          Connect your vector database to store your embeddings in your own
          databases.
        </p>
      </div>
      {loading ? (
        <Loading />
      ) : (
        <div className="flex-col border-b">
          {siteConfig.vectorDbs.map((vectorDb) => (
            <div
              className="flex items-center justify-between border-t py-4"
              key={vectorDb.provider}
            >
              <div className="flex items-center space-x-4">
                <Image
                  src={vectorDb.logo}
                  width="40"
                  height="40"
                  alt={vectorDb.name}
                />
                <p className="font-medium">{vectorDb.name}</p>
              </div>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  Settings
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
