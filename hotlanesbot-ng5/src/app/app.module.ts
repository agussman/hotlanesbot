import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MaterialModule } from './material.module';

import { LeafletModule } from '@asymmetrik/ngx-leaflet';
import { SidenavDrawerOverviewComponent } from './sidenav-drawer-overview/sidenav-drawer-overview.component';

@NgModule({
  declarations: [
    AppComponent,
    SidenavDrawerOverviewComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MaterialModule,
    LeafletModule.forRoot()
  ],
  providers: [],
  bootstrap: [AppComponent]
})


export class AppModule { }
