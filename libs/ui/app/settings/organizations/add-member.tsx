  'use client'
  import React from 'react';
  import { useForm } from "react-hook-form";
  import { zodResolver } from "@hookform/resolvers/zod";
  import zod from "zod";
  import * as z from "zod";
  import { useToast } from "@/components/ui/use-toast"
  import { Toaster } from "@/components/ui/toaster"
  import { useState } from 'react';
  import { useRouter } from "next/navigation"

  import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
  } from "@/components/ui/dialog";
  import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
  } from "@/components/ui/form";
  import { Input } from "@/components/ui/input";
  import { Button, buttonVariants } from "@/components/ui/button";
  import { cn } from "@/lib/utils";
  import { Spinner } from "@/components/ui/spinner";
  import { Organization } from '@/types/organization';

  interface AddMemberToOrganizationProps {
    organization: Organization;
  }

  const formSchema = z.object({
    profileId: z.string()
      .transform((value) => {
        const parsed = parseInt(value, 10);
        return isNaN(parsed) ? 0 : parsed;
      })
      .refine((val) => val > 0, {
        message: "Profile ID must be a positive number",
      }),
  });


  type FormValues = z.infer<typeof formSchema>;

  export default function AddMemberToOrganization({ organization }: AddMemberToOrganizationProps) {
    const router = useRouter()
    const { toast } = useToast();
    const [feedback, setFeedback] = useState('');
    const [email, setEmail] = useState('');

    const { ...form } = useForm<z.infer<typeof formSchema>>({
      resolver: zodResolver(formSchema),
      defaultValues: {
        profileId: 0,
      },
      })

    async function onSubmit(values: z.infer<typeof formSchema>) {
      try {
        const { profileId } = values;
        const response = await fetch('/organizations/addMember', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ profileId: profileId, organizationId: organization.id })
        });

        const result = await response.json();

        if (response.ok) {
          toast({ description: "Member added successfully to " + organization.name });
        } else {
          toast({ description: `Error: ${result.error}`, variant: "destructive" });
        }
        router.refresh()
        router.push(`/settings/organizations`)
      } catch (error: any) {
        toast({
          description: error?.message,
          variant: "destructive",
        })
      }
    };

    return (
      <div className="flex min-h-screen flex-col justify-center">
        <div className="container max-w-lg">
          <Dialog>
          <DialogTrigger className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
            <p>Add Member to {organization.name}</p>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Member to {organization.name}</DialogTitle>
              <DialogDescription>
                Enter the user's id to add them to your organization.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-4">
                <div className="flex flex-col space-y-2">
                  <FormField
                    control={form.control}
                    name="profileId"
                    render={({ field }) => (
                      <FormItem className="flex-1">
                        <FormLabel>User ID</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Enter profile ID"
                            {...field}
                            required
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <DialogFooter>
                  <Button type="submit" size="sm" className="w-full">
                    {form.control._formState.isSubmitting ? (<Spinner />) : ("Add User")}
                  </Button>
                </DialogFooter>
              </form>
              {feedback && <p>{feedback}</p>}
            </Form>
          </DialogContent>
          </Dialog>
        </div>
        <Toaster />
      </div>
    );
  }
