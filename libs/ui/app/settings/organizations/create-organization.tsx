'use client';
import { useState } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';
import Stripe from "stripe"
import md5 from 'md5'; // Assuming md5 is installed
import { stripe } from "@/lib/stripe"
import { useRouter } from "next/navigation"


import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useForm } from "react-hook-form";
import zod from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Api } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { Spinner } from "@/components/ui/spinner"
import { Profile } from '@/types/profile';



const formSchema = zod.object({
    name: z.string().nonempty({message: "Organization name is required"}),
    options: z.record(z.any()),
    // Add more fields as necessary
  });

  
interface CreateOrganizationProps {
    profile: Profile;
    user: any;
    // You can also pass profile if needed
  };
  
export default function CreateOrganization({ profile, user }: CreateOrganizationProps) {
    const router = useRouter()
    const api = new Api()
    const [name, setName] = useState('');
    const [feedback, setFeedback] = useState('');
    const supabase = createClientComponentClient();
    const { toast } = useToast()
    const { ...form } = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
        name: "",
        options: {},
    },
    })

    async function onSubmit(values: z.infer<typeof formSchema>) {
        try {
            const { name } = values;
            if (!user) {
                setFeedback("User is not authenticated.");
                return;
            }

            // Create Stripe customer
            const params: Stripe.CustomerCreateParams = { name: name };
            let customer: Stripe.Customer | null = null;
            if (process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY) {
                customer = await stripe.customers.create(params);
            }

            if (!user?.email) {
                toast({ description: `Ooops! User email is missing!`, variant: "destructive" });
                return;
            }

            // Generate the API key and slug
            const { data: { token: api_key } } = await api.createApiKey(user.email);
            const slug = 'org-' + md5(new Date().toISOString() + Math.random().toString(36)).substring(0, 8);

            // Create organization in Supabase
            console.log('Inserting row into organizations table...')

            const { data: orgData, error: orgError } = await supabase
                .from('organizations')
                .insert(
                    { 
                    name, 
                    api_key, 
                    stripe_customer_id: customer?.id, 
                    is_onboarded: true, 
                    is_personal: false, 
                    slug 
                    }
                )
                .select()
                

            if (orgError) {
                toast({
                    description: `Error creating organization: ${orgError.message}`,
                    variant: "destructive",
                })
                return;
            }

            const organizationId = orgData ? orgData[0].id : null;

            // Attempt to link organization with user's profile
            const { error: linkError } = await supabase
                .from('profile_organization')
                .insert(
                    { profile_id: profile.id, organization_id: organizationId }
                );

            if (linkError) {
                // Rollback: Delete the newly created organization
                await supabase
                    .from('organizations')
                    .delete()
                    .match({ id: organizationId });

                toast({
                    description: `Error linking organization: ${linkError.message}`,
                    variant: "destructive",
                })
                return;
            }
            
            // If we get this far, everything worked!
            toast({ description: "Organization created!" });
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
            <DialogTrigger
                    className={cn(buttonVariants({ variant: "default", size: "sm" }))}
            >
                <p>Create New Organization</p>
            </DialogTrigger>
            <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Create New Organization</DialogTitle>
                        <DialogDescription>
                        Enter details to create a new organization.
                        </DialogDescription>
                    </DialogHeader>
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-4">
                            <div className="flex flex-col space-y-2">
                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem className="flex-1">
                                            <FormLabel>Organization Name</FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="Enter your organization name"
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
                                    {form.control._formState.isSubmitting ? (
                                                    <Spinner />
                                                    ) : (
                                                    "Create Organization"
                                                    )}
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
