import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, ShieldAlert, Zap, LayoutDashboard, History, Crosshair } from "lucide-react"

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
          ORBIT <span className="text-muted-foreground text-2xl font-medium ml-2">Dashboard</span>
        </h1>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="text-sm font-medium">Ollama Connected</span>
          </div>
        </div>
      </header>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 h-auto p-1 bg-muted/50 rounded-xl">
          <TabsTrigger value="overview" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <LayoutDashboard className="w-4 h-4 mr-2" /> Overview
          </TabsTrigger>
          <TabsTrigger value="runs" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <History className="w-4 h-4 mr-2" /> Runs
          </TabsTrigger>
          <TabsTrigger value="security" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <ShieldAlert className="w-4 h-4 mr-2" /> Security
          </TabsTrigger>
          <TabsTrigger value="arena" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Crosshair className="w-4 h-4 mr-2" /> Arena
          </TabsTrigger>
          <TabsTrigger value="replay" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Activity className="w-4 h-4 mr-2" /> Replay
          </TabsTrigger>
          <TabsTrigger value="models" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
            <Zap className="w-4 h-4 mr-2" /> Models
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border/50 shadow-sm transition-all hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
                <History className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">128</div>
                <p className="text-xs text-muted-foreground">+14% from last hour</p>
              </CardContent>
            </Card>
            <Card className="border-border/50 shadow-sm transition-all hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average ARI</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-500">89.4</div>
                <p className="text-xs text-muted-foreground">Excellent</p>
              </CardContent>
            </Card>
            <Card className="border-border/50 shadow-sm transition-all hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Security Alerts</CardTitle>
                <ShieldAlert className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-destructive">3</div>
                <p className="text-xs text-muted-foreground">Requires attention</p>
              </CardContent>
            </Card>
            <Card className="border-border/50 shadow-sm transition-all hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Models</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">4</div>
                <p className="text-xs text-muted-foreground">llama3.1, qwen2.5...</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="runs">
            <Card>
                <CardHeader>
                    <CardTitle>Recent Runs</CardTitle>
                    <CardDescription>A complete history of agent executions.</CardDescription>
                </CardHeader>
                <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground">
                    Runs table will be implemented here.
                </CardContent>
            </Card>
        </TabsContent>
        <TabsContent value="security">
            <Card>
                <CardHeader>
                    <CardTitle>Security Events</CardTitle>
                    <CardDescription>Detected prompt injections and policy violations.</CardDescription>
                </CardHeader>
                <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground">
                    Security dashboard will be implemented here.
                </CardContent>
            </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default App
